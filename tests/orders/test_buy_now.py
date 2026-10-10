from decimal import Decimal
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from orders.models import Order
from orders.services import OrderCreationError, create_order
from payments.mercadopago import MercadoPagoError
from products.models import Category, Product


@pytest.fixture
def purchase_products(db):
    category = Category.objects.create(name="Painéis", slug="paineis-direto")
    return [
        Product.objects.create(
            category=category, name=f"Painel {number}", slug=f"painel-direto-{number}",
            price=Decimal("100.00") * number, stock=5,
        )
        for number in [1, 2]
    ]


def start_url(product):
    return reverse("orders:buy_now", kwargs={"product_id": product.pk})


def checkout_url(product, quantity=1):
    return reverse("orders:direct_checkout", kwargs={"product_id": product.pk, "quantity": quantity})


def customer_data():
    return {
        "customer_name": "Cliente", "customer_email": "cliente@example.com",
        "customer_phone": "11999999999", "shipping_postal_code": "01001-000",
        "shipping_address": "Praça da Sé", "shipping_number": "1",
        "shipping_complement": "", "shipping_neighborhood": "Sé",
        "shipping_city": "São Paulo", "shipping_state": "SP",
    }


@pytest.mark.django_db
@pytest.mark.parametrize("quantity", [1, 3])
def test_buy_now_opens_only_selected_product_and_preserves_cart(client, purchase_products, quantity):
    product, other = purchase_products
    client.post(reverse("orders:cart_add", kwargs={"product_id": other.pk}), {"quantity": 2})
    expected_cart = {str(other.pk): 2}

    response = client.post(start_url(product), {"quantity": quantity}, follow=True)

    assert response.redirect_chain == [(checkout_url(product, quantity), 302)]
    assert response.context["direct_purchase"] is True
    assert response.context["items"] == [{
        "product": product, "quantity": quantity, "subtotal": product.price * quantity,
    }]
    assert response.context["cart_total"] == product.price * quantity
    assert client.session["cart"] == expected_cart
    assert not Order.objects.exists()
    product.refresh_from_db()
    assert product.stock == 5


@pytest.mark.django_db
def test_direct_purchase_without_cart_and_default_quantity(client, purchase_products):
    product = purchase_products[0]
    response = client.post(start_url(product), follow=True)
    assert response.status_code == 200
    assert response.context["items"][0]["quantity"] == 1
    assert client.session.get("cart", {}) == {}


@pytest.mark.django_db
def test_separate_direct_checkout_urls_do_not_overwrite_each_other(client, purchase_products):
    first, second = purchase_products
    first_response = client.post(start_url(first), {"quantity": 2})
    second_response = client.post(start_url(second), {"quantity": 3})
    assert client.get(first_response.url).context["items"][0]["product"] == first
    assert client.get(second_response.url).context["items"][0]["product"] == second
    assert client.get(first_response.url).context["items"][0]["quantity"] == 2


@pytest.mark.django_db
@pytest.mark.parametrize("quantity", ["", "abc", "0", "-1", "6", "1.5"])
def test_buy_now_rejects_invalid_quantity(client, purchase_products, quantity):
    product = purchase_products[0]
    response = client.post(start_url(product), {"quantity": quantity})
    assert response.url == reverse("products:product_detail", kwargs={"slug": product.slug})
    assert not Order.objects.exists()
    assert client.session.get("cart", {}) == {}


@pytest.mark.django_db
@pytest.mark.parametrize("unavailable", ["product", "category", "course", "stock"])
def test_direct_purchase_rejects_unavailable_products(client, purchase_products, unavailable):
    product = purchase_products[0]
    if unavailable == "product":
        product.is_active = False
    elif unavailable == "category":
        product.category.is_active = False
        product.category.save()
    elif unavailable == "course":
        product.product_type = Product.ProductType.COURSE
    else:
        product.stock = 0
    product.save()
    expected_status = 302 if unavailable == "stock" else 404
    assert client.post(start_url(product)).status_code == expected_status
    assert client.get(checkout_url(product)).status_code == expected_status
    assert client.post(checkout_url(product), customer_data()).status_code == expected_status
    assert not Order.objects.exists()


@pytest.mark.django_db
def test_buy_now_requires_post_and_csrf(client, purchase_products):
    product = purchase_products[0]
    assert client.get(start_url(product)).status_code == 405
    csrf_client = Client(enforce_csrf_checks=True)
    assert csrf_client.post(start_url(product)).status_code == 403
    assert csrf_client.post(checkout_url(product), customer_data()).status_code == 403


@pytest.mark.django_db
def test_direct_order_uses_current_price_reserves_stock_and_preserves_same_product_cart(client, purchase_products):
    product, other = purchase_products
    for item in purchase_products:
        client.post(reverse("orders:cart_add", kwargs={"product_id": item.pk}), {"quantity": 1})
    expected_cart = {str(product.pk): 1, str(other.pk): 1}
    token = client.get(checkout_url(product, 2)).context["checkout_token"]
    product.price = Decimal("125.00")
    product.save()
    payload = {**customer_data(), "checkout_token": token, "price": "0.01", "total": "0.01", "quantity": "5"}
    with patch("orders.views.create_checkout_order", return_value={
        "id": "direct-payment", "checkout_url": "https://www.mercadopago.com.br/checkout/test",
    }) as provider:
        response = client.post(checkout_url(product, 2), payload)
    order = Order.objects.get()
    item = order.items.get()
    product.refresh_from_db()
    other.refresh_from_db()
    assert response.status_code == 302
    assert response.url == "https://www.mercadopago.com.br/checkout/test"
    assert item.product == product
    assert item.quantity == 2
    assert item.unit_price == Decimal("125.00")
    assert order.total == Decimal("250.00")
    assert product.stock == 3
    assert other.stock == 5
    assert client.session["cart"] == expected_cart
    assert order.provider_order_id == "direct-payment"
    provider.assert_called_once()


@pytest.mark.django_db
def test_failed_direct_payment_releases_stock_preserves_cart_and_allows_retry(client, purchase_products):
    product, other = purchase_products
    client.post(reverse("orders:cart_add", kwargs={"product_id": other.pk}))
    data = customer_data()
    data["checkout_token"] = client.get(checkout_url(product, 2)).context["checkout_token"]
    with patch("orders.views.create_checkout_order", side_effect=MercadoPagoError("Pagamento indisponível")):
        response = client.post(checkout_url(product, 2), data)
    product.refresh_from_db()
    assert response.status_code == 200
    assert "Pagamento indisponível" in response.content.decode()
    assert Order.objects.get().status == Order.Status.CANCELED
    assert product.stock == 5
    assert client.session["cart"] == {str(other.pk): 1}
    assert client.get(checkout_url(product, 2)).context["items"][0]["quantity"] == 2


@pytest.mark.django_db
def test_direct_checkout_rechecks_stock_before_payment(client, purchase_products):
    product = purchase_products[0]
    client.get(checkout_url(product, 3))
    product.stock = 2
    product.save()
    with patch("orders.views.create_checkout_order") as provider:
        response = client.post(checkout_url(product, 3), customer_data())
    assert response.status_code == 302
    assert not Order.objects.exists()
    provider.assert_not_called()


@pytest.mark.django_db
def test_order_service_rejects_stock_change_inside_transaction(client, purchase_products):
    product = purchase_products[0]
    with pytest.raises(OrderCreationError):
        create_order(client, customer_data(), {product.pk: product.stock + 1})
    product.refresh_from_db()
    assert product.stock == 5
    assert not Order.objects.exists()


@pytest.mark.django_db
def test_invalid_direct_checkout_form_does_not_reserve_stock(client, purchase_products):
    product = purchase_products[0]
    with patch("orders.views.create_checkout_order") as provider:
        response = client.post(checkout_url(product), {"customer_name": "Cliente"})
    assert response.status_code == 200
    assert response.context["form"].errors
    assert not Order.objects.exists()
    provider.assert_not_called()
