from django.contrib import messages
from datetime import timedelta
from uuid import UUID

from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone

from payments.mercadopago import MercadoPagoError, MercadoPagoUncertainError, create_checkout_order
from products.models import Product

from .cart import Cart
from .forms import CheckoutForm, PurchaseQuantityForm
from .models import CheckoutAttempt, Order
from .services import (
    OrderCreationError, cancel_order, claim_checkout_attempt, issue_checkout_attempt,
)


def cart_detail(request):
    cart = Cart(request)
    return render(
        request,
        "orders/cart_detail.html",
        {"cart": cart, "items": cart.items(), "cart_total": cart.total()},
    )


def cart_add(request, product_id):
    product = get_object_or_404(
        Product,
        pk=product_id,
        is_active=True,
        category__is_active=True,
        product_type=Product.ProductType.PHYSICAL,
    )
    quantity = request.POST.get("quantity", "1")
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 1
    if product.stock <= 0:
        messages.error(request, "Este produto está sem estoque.")
    else:
        Cart(request).add(product, quantity)
        messages.success(request, "Produto adicionado ao carrinho.")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        cart = Cart(request)
        items = cart.items()
        return JsonResponse(
            {
                "html": render_to_string(
                    "orders/partials/cart_drawer_content.html",
                    {
                        "cart_items": items,
                        "cart_total": sum((item["subtotal"] for item in items), 0),
                    },
                    request=request,
                ),
                "cart_count": sum(item["quantity"] for item in items),
            }
        )
    return redirect(request.POST.get("next") or "orders:cart_detail")


def cart_update(request, product_id):
    product = get_object_or_404(
        Product,
        pk=product_id,
        product_type=Product.ProductType.PHYSICAL,
    )
    quantity = request.POST.get("quantity", "0")
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 0
    Cart(request).set_quantity(product, quantity)
    return redirect("orders:cart_detail")


def cart_remove(request, product_id):
    product = get_object_or_404(
        Product,
        pk=product_id,
        product_type=Product.ProductType.PHYSICAL,
    )
    Cart(request).remove(product)
    return redirect("orders:cart_detail")


@require_POST
def buy_now(request, product_id):
    product = get_object_or_404(
        Product, pk=product_id, is_active=True, category__is_active=True,
        product_type=Product.ProductType.PHYSICAL,
    )
    quantity_form = PurchaseQuantityForm(
        {"quantity": request.POST.get("quantity", "1")}, stock=product.stock,
    )
    if not quantity_form.is_valid():
        messages.error(request, "Informe uma quantidade disponível em estoque.")
        return redirect("products:product_detail", slug=product.slug)
    return redirect(
        "orders:direct_checkout", product_id=product.pk,
        quantity=quantity_form.cleaned_data["quantity"],
    )


def _existing_checkout_response(order):
    if (
        order.status == Order.Status.PENDING_PAYMENT
        and order.checkout_url
        and order.created_at > timezone.now() - timedelta(days=1)
    ):
        return redirect(order.checkout_url)
    return redirect("order_confirmation", number=order.number, result="pendente")


def checkout(request, product_id=None, quantity=None):
    attempt = None
    if request.method == "POST" and request.POST.get("checkout_token"):
        try:
            token = UUID(request.POST["checkout_token"])
        except (ValueError, TypeError):
            return HttpResponseBadRequest("Abra o checkout novamente.")
        attempt = CheckoutAttempt.objects.filter(
            pk=token, session_key=request.session.session_key, checkout_path=request.path,
        ).first()
        if not attempt:
            return HttpResponseBadRequest("Abra o checkout novamente.")
        if attempt.order_id:
            return _existing_checkout_response(Order.objects.get(pk=attempt.order_id))

    direct_purchase = product_id is not None
    if direct_purchase:
        product = get_object_or_404(
            Product.objects.select_related("category"), pk=product_id,
            is_active=True, category__is_active=True,
            product_type=Product.ProductType.PHYSICAL,
        )
        quantity_form = PurchaseQuantityForm({"quantity": quantity}, stock=product.stock)
        if not quantity_form.is_valid():
            messages.error(request, "A quantidade escolhida não está mais disponível.")
            return redirect("products:product_detail", slug=product.slug)
        items = [{"product": product, "quantity": quantity, "subtotal": product.price * quantity}]
        checkout_total = items[0]["subtotal"]
    else:
        cart = Cart(request)
        items = cart.items()
        if not items:
            return redirect("orders:cart_detail")
        checkout_total = cart.total()

    form = CheckoutForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        if not attempt:
            return HttpResponseBadRequest("Abra o checkout novamente.")
        order = None
        try:
            customer_data = form.cleaned_data.copy()
            customer_data.pop("saved_address", None)
            order, created = claim_checkout_attempt(
                request, attempt, customer_data, direct_purchase=direct_purchase,
            )
            if not created:
                return _existing_checkout_response(order)
            provider_order = create_checkout_order(order)
        except MercadoPagoUncertainError as error:
            form.add_error(None, str(error))
        except (OrderCreationError, MercadoPagoError) as error:
            if order is not None:
                cancel_order(order)
                # An explicit rejection allows a new attempt; old retries stay consumed.
                attempt = None
            form.add_error(None, str(error))
        else:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(pk=order.pk)
                order.provider_order_id = order.provider_order_id or provider_order["id"]
                order.provider_status = order.provider_status or provider_order.get("status", "created")
                order.checkout_url = provider_order["checkout_url"]
                order.save(update_fields=["provider_order_id", "provider_status", "checkout_url", "updated_at"])
            if not direct_purchase:
                Cart(request).clear()
            return redirect(order.checkout_url)

    attempt = attempt or issue_checkout_attempt(request, items)
    return render(
        request,
        "orders/checkout.html",
        {
            "form": form, "items": items, "cart_total": checkout_total,
            "checkout_token": str(attempt.pk),
            "direct_purchase": direct_purchase,
            "checkout_action": (
                reverse("orders:direct_checkout", kwargs={"product_id": product_id, "quantity": quantity})
                if direct_purchase else reverse("orders:checkout")
            ),
        },
    )


def order_confirmation(request, number, result):
    order = get_object_or_404(Order, number=number)
    return render(request, "orders/order_confirmation.html", {"order": order, "result": result})
