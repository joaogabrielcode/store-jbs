from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from products.models import Product

from .cart import Cart
from .models import CheckoutAttempt, Order, OrderItem


class OrderCreationError(Exception):
    pass


class OrderStatusTransitionError(Exception):
    pass


@transaction.atomic
def create_order_from_cart(request, customer_data):
    cart = Cart(request)
    requested_items = {
        int(product_id): int(quantity)
        for product_id, quantity in cart.data.items()
        if int(quantity) > 0
    }
    if not requested_items:
        raise OrderCreationError("O carrinho está vazio.")

    order = create_order(request, customer_data, requested_items)
    cart.clear()
    return order


@transaction.atomic
def create_order(request, customer_data, requested_items):
    if not requested_items or any(quantity < 1 for quantity in requested_items.values()):
        raise OrderCreationError("Informe uma quantidade válida.")

    products = Product.objects.select_for_update().filter(
        id__in=requested_items,
        is_active=True,
        category__is_active=True,
        product_type=Product.ProductType.PHYSICAL,
    )
    products_by_id = {product.id: product for product in products}
    if len(products_by_id) != len(requested_items):
        raise OrderCreationError("Um dos produtos não está mais disponível.")

    subtotal = Decimal("0.00")
    order_items = []
    for product_id, requested_quantity in requested_items.items():
        product = products_by_id[product_id]
        if requested_quantity > product.stock:
            raise OrderCreationError(
                f"Estoque insuficiente para {product.name}. Disponível: {product.stock}."
            )
        item_subtotal = product.price * requested_quantity
        subtotal += item_subtotal
        order_items.append(
            {"product": product, "quantity": requested_quantity, "subtotal": item_subtotal}
        )

    shipping_cost = Decimal("0.00")
    request_user = getattr(request, "user", None)
    order = Order.objects.create(
        user=request_user if request_user and request_user.is_authenticated else None,
        **customer_data,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=subtotal + shipping_cost,
    )
    for item in order_items:
        OrderItem.objects.create(
            order=order,
            product=item["product"],
            product_name=item["product"].name,
            unit_price=item["product"].price,
            quantity=item["quantity"],
            subtotal=item["subtotal"],
        )
        item["product"].stock -= item["quantity"]
        item["product"].save(update_fields=["stock", "updated_at"])

    return order


@transaction.atomic
def mark_order_as_paid(order):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status == Order.Status.PAID:
        return order
    if order.status != Order.Status.PENDING_PAYMENT:
        raise OrderStatusTransitionError(
            f"Não é possível marcar o pedido {order.number} como pago a partir de "
            f"{order.status}."
        )
    order.status = Order.Status.PAID
    order.save(update_fields=["status", "updated_at"])
    return order


@transaction.atomic
def cancel_order(order):
    order = Order.objects.select_for_update().get(pk=order.pk)
    update_fields = ["status", "updated_at"]
    if order.stock_released_at is None:
        for item in order.items.all():
            if item.product_id is not None:
                Product.objects.filter(pk=item.product_id).update(
                    stock=F("stock") + item.quantity
                )
        order.stock_released_at = timezone.now()
        update_fields.append("stock_released_at")
    order.status = Order.Status.CANCELED
    order.save(update_fields=update_fields)
    return order


def release_order_stock(order):
    """Cancel an order and release its reserved stock exactly once."""
    return cancel_order(order)


def issue_checkout_attempt(request, items):
    if not request.session.session_key:
        request.session.create()
    return CheckoutAttempt.objects.create(
        session_key=request.session.session_key,
        checkout_path=request.path,
        items={str(item["product"].pk): item["quantity"] for item in items},
    )


@transaction.atomic
def claim_checkout_attempt(request, attempt, customer_data, *, direct_purchase):
    attempt = CheckoutAttempt.objects.select_for_update().get(
        pk=attempt.pk, session_key=request.session.session_key, checkout_path=request.path
    )
    if attempt.order_id:
        return Order.objects.get(pk=attempt.order_id), False
    if attempt.created_at <= timezone.now() - timedelta(days=1):
        raise OrderCreationError("Esta tentativa expirou. Abra o checkout novamente.")
    if not direct_purchase:
        current_items = {
            str(item["product"].pk): item["quantity"] for item in Cart(request).items()
        }
        if current_items != attempt.items:
            raise OrderCreationError("O carrinho mudou. Abra o checkout novamente.")
    order = create_order(
        request, customer_data,
        {int(product_id): quantity for product_id, quantity in attempt.items.items()},
    )
    attempt.order = order
    attempt.save(update_fields=["order"])
    return order, True
