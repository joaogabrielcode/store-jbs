import json
import hashlib
import hmac
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse

from orders.models import Order
from orders.services import (
    OrderCreationError,
    cancel_order,
    create_order_from_cart,
    mark_order_as_paid,
)
from products.models import Category, Product


@pytest.fixture
def order_product(db):
    category = Category.objects.create(name="Inversores", slug="inversores")
    return Product.objects.create(
        category=category,
        name="Inversor 5kW",
        slug="inversor-5kw",
        price=Decimal("1200.00"),
        stock=3,
    )


def checkout_data():
    return {
        "customer_name": "João Cliente",
        "customer_email": "cliente@example.com",
        "customer_phone": "11999999999",
        "shipping_postal_code": "01001-000",
        "shipping_address": "Praça da Sé",
        "shipping_number": "1",
        "shipping_complement": "Apto 2",
        "shipping_neighborhood": "Sé",
        "shipping_city": "São Paulo",
        "shipping_state": "SP",
    }


@pytest.mark.django_db
def test_create_order_reserves_stock_and_snapshots_price(client, order_product):
    client.post(
        reverse("orders:cart_add", kwargs={"product_id": order_product.id}),
        {"quantity": 2},
    )

    order = create_order_from_cart(client, checkout_data())

    order_product.refresh_from_db()
    item = order.items.get()
    assert order.status == Order.Status.PENDING_PAYMENT
    assert order.subtotal == Decimal("2400.00")
    assert order.total == Decimal("2400.00")
    assert order_product.stock == 1
    assert item.product_name == "Inversor 5kW"
    assert item.unit_price == Decimal("1200.00")
    client.session.save()
    assert client.session["cart"] == {}


@pytest.mark.django_db
def test_order_creation_rejects_insufficient_stock_without_changing_stock(client, order_product):
    client.post(
        reverse("orders:cart_add", kwargs={"product_id": order_product.id}),
        {"quantity": 1},
    )
    session = client.session
    session["cart"] = {str(order_product.id): 4}
    session.save()

    with pytest.raises(OrderCreationError):
        create_order_from_cart(client, checkout_data())

    order_product.refresh_from_db()
    assert order_product.stock == 3
    assert not Order.objects.exists()


@pytest.mark.django_db
def test_checkout_requires_configured_mercado_pago(client, order_product, settings):
    settings.MERCADOPAGO_ACCESS_TOKEN = ""
    client.post(
        reverse("orders:cart_add", kwargs={"product_id": order_product.id}),
        {"quantity": 1},
    )

    data = checkout_data()
    data["checkout_token"] = client.get(reverse("orders:checkout")).context["checkout_token"]
    response = client.post(reverse("orders:checkout"), data)

    assert response.status_code == 200
    assert "não configurado" in response.content.decode()
    order_product.refresh_from_db()
    assert order_product.stock == 3


@pytest.mark.django_db
def test_order_status_transition_to_paid_is_idempotent(client, order_product):
    client.post(
        reverse("orders:cart_add", kwargs={"product_id": order_product.id}),
        {"quantity": 1},
    )
    order = create_order_from_cart(client, checkout_data())

    mark_order_as_paid(order)
    mark_order_as_paid(order)

    order.refresh_from_db()
    assert order.status == Order.Status.PAID


@pytest.mark.django_db
def test_cancel_order_releases_stock_only_once(client, order_product):
    client.post(
        reverse("orders:cart_add", kwargs={"product_id": order_product.id}),
        {"quantity": 2},
    )
    order = create_order_from_cart(client, checkout_data())

    cancel_order(order)
    cancel_order(order)

    order_product.refresh_from_db()
    order.refresh_from_db()
    assert order.status == Order.Status.CANCELED
    assert order.stock_released_at is not None
    assert order_product.stock == 3


@pytest.mark.django_db
def test_mercadopago_webhook_synchronizes_and_repeats_safely(
    client, order_product, settings
):
    settings.DEBUG = True
    settings.MERCADOPAGO_WEBHOOK_SECRET = "test-secret"
    manifest = "id:provider-order-id;request-id:test-request;ts:1700000000;"
    signature = hmac.new(b"test-secret", manifest.encode(), hashlib.sha256).hexdigest()
    headers = {"HTTP_X_REQUEST_ID": "test-request", "HTTP_X_SIGNATURE": f"ts=1700000000,v1={signature}"}
    client.post(
        reverse("orders:cart_add", kwargs={"product_id": order_product.id}),
        {"quantity": 1},
    )
    order = create_order_from_cart(client, checkout_data())
    order.provider_order_id = "provider-order-id"
    order.save(update_fields=["provider_order_id", "updated_at"])

    with patch(
        "payments.services.fetch_order",
        return_value={"id": "provider-order-id", "status": "processed", "status_detail": "accredited", "external_reference": str(order.number), "total_amount": str(order.total)},
    ):
        payload = {"data": {"id": "provider-order-id"}}
        first_response = client.post(
            reverse("payments:mercadopago_webhook") + "?data.id=provider-order-id",
            **headers,
            data=json.dumps(payload),
            content_type="application/json",
        )
        second_response = client.post(
            reverse("payments:mercadopago_webhook") + "?data.id=provider-order-id",
            **headers,
            data=json.dumps(payload),
            content_type="application/json",
        )

    order.refresh_from_db()
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert order.status == Order.Status.PAID


def test_mercadopago_webhook_requires_signature_secret_in_production(client, settings):
    settings.DEBUG = False
    settings.MERCADOPAGO_WEBHOOK_SECRET = ""

    response = client.post(
        reverse("payments:mercadopago_webhook"),
        data=json.dumps({"data": {"id": "provider-order-id"}}),
        content_type="application/json",
    )

    assert response.status_code == 503
