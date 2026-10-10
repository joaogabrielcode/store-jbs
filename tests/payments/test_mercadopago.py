import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
import requests
from django.urls import reverse

from orders.models import Order
from orders.services import create_order
from payments.mercadopago import MercadoPagoError, MercadoPagoUncertainError, create_checkout_order, fetch_order
from payments.services import synchronize_mercadopago_order
from products.models import Category, Product


@pytest.fixture
def order(client, db):
    category = Category.objects.create(name="Painéis", slug="mp-paineis")
    product = Product.objects.create(category=category, name="Painel", slug="mp-painel", price=Decimal("100.00"), stock=5)
    return create_order(client, {
        "customer_name": "Cliente", "customer_email": "client@example.com", "customer_phone": "11999999999",
        "shipping_postal_code": "01001-000", "shipping_address": "Praça da Sé", "shipping_number": "1",
        "shipping_neighborhood": "Sé", "shipping_city": "São Paulo", "shipping_state": "SP",
    }, {product.pk: 2})


@pytest.fixture
def credentials(settings):
    settings.DEBUG = True
    settings.MERCADOPAGO_ACCESS_TOKEN = "test-token"
    settings.MERCADOPAGO_WEBHOOK_SECRET = "test-secret"
    settings.SITE_URL = "http://localhost:8000"


def remote(order, status="processed", detail="accredited"):
    return {"id": "ORDTest123", "external_reference": str(order.number), "total_amount": str(order.total), "status": status, "status_detail": detail}


def signed_headers(provider_id="ORDTest123"):
    manifest = f"id:{provider_id};request-id:test-request;ts:1700000000;"
    digest = hmac.new(b"test-secret", manifest.encode(), hashlib.sha256).hexdigest()
    return {"HTTP_X_SIGNATURE": f"ts=1700000000,v1={digest}", "HTTP_X_REQUEST_ID": "test-request"}


@pytest.mark.django_db
def test_orders_api_payload_backend_prices_return_urls_and_stable_idempotency(order, credentials):
    result = {"id": "ORDTest123", "checkout_url": "https://www.mercadopago.com.br/checkout/test"}
    with patch("payments.mercadopago.requests.post", return_value=Mock(status_code=201, json=Mock(return_value=result))) as post:
        assert create_checkout_order(order) == result
        create_checkout_order(order)
    first, second = post.call_args_list
    assert first.kwargs["headers"]["X-Idempotency-Key"] == second.kwargs["headers"]["X-Idempotency-Key"] == str(order.number)
    assert first.args[0].endswith("/v1/orders")
    payload = first.kwargs["json"]
    assert payload["expiration_time"] == "P1D"
    assert payload["total_amount"] == "200.00" and payload["external_reference"] == str(order.number)
    assert payload["items"][0]["quantity"] == 2 and payload["items"][0]["unit_price"] == "100.00"
    assert payload["config"]["redirect_urls"]["success"] == f"http://localhost:8000/pedidos/{order.number}/sucesso/"
    assert first.kwargs["timeout"] == 15 and not first.kwargs["allow_redirects"]


@pytest.mark.django_db
@pytest.mark.parametrize("status,detail,expected", [
    ("created", "created", "pending_payment"), ("processing", "in_process", "pending_payment"),
    ("action_required", "waiting_capture", "pending_payment"), ("processed", "accredited", "paid"),
    ("failed", "rejected_by_issuer", "canceled"), ("canceled", "canceled", "canceled"),
    ("processed", "refunded", "refunded"), ("refunded", "refunded", "refunded"),
    ("processed", "partially_refunded", "paid")])
def test_authoritative_states_repeat_idempotently(order, status, detail, expected):
    with patch("payments.services.fetch_order", return_value=remote(order, status, detail)):
        synchronize_mercadopago_order("ORDTest123")
        synchronize_mercadopago_order("ORDTest123")
    order.refresh_from_db()
    assert order.status == expected
    product = order.items.get().product
    assert product.stock == (5 if expected == "canceled" else 3)


@pytest.mark.django_db
@pytest.mark.parametrize("tamper", ["id", "external_reference", "total_amount", "missing", "nan", "provider_id"])
def test_rejects_unmatched_payment_without_mutating_order(order, tamper):
    data = remote(order)
    if tamper == "missing": data.pop("total_amount")
    elif tamper == "nan": data["total_amount"] = "NaN"
    elif tamper == "provider_id":
        order.provider_order_id = "AnotherOrder"
        order.save()
    else: data[tamper] = "1"
    with patch("payments.services.fetch_order", return_value=data):
        with pytest.raises(MercadoPagoError): synchronize_mercadopago_order("ORDTest123")
    order.refresh_from_db()
    assert order.status == Order.Status.PENDING_PAYMENT


@pytest.mark.django_db
def test_notifications_dont_regress_fulfillment_or_restock_refunds(order):
    order.status = Order.Status.SHIPPED
    order.save()
    with patch("payments.services.fetch_order", return_value=remote(order)):
        synchronize_mercadopago_order("ORDTest123")
    order.refresh_from_db()
    assert order.status == Order.Status.SHIPPED
    with patch("payments.services.fetch_order", return_value=remote(order, "processed", "refunded")):
        synchronize_mercadopago_order("ORDTest123")
    assert order.items.get().product.stock == 3
    with patch("payments.services.fetch_order", return_value=remote(order)):
        with pytest.raises(MercadoPagoError): synchronize_mercadopago_order("ORDTest123")


@pytest.mark.django_db
def test_webhook_signature_exact_case_retries_and_malformed_payloads(client, order, credentials):
    url = reverse("payments:mercadopago_webhook") + "?data.id=ORDTest123&type=order"
    with patch("payments.services.fetch_order", return_value=remote(order)) as fetch:
        assert client.post(url, json.dumps({"data": {"id": "ORDTest123"}}), content_type="application/json", **signed_headers()).status_code == 200
        assert client.post(url, "{}", content_type="application/json", **signed_headers()).status_code == 200
        assert client.post(url, "{}", content_type="application/json", **signed_headers("ordtest123")).status_code == 403
        assert client.post(url, "[]", content_type="application/json", **signed_headers()).status_code == 400
        assert client.post(url, '{"data": []}', content_type="application/json", **signed_headers()).status_code == 400
        assert client.post(url, '{"data": {"id":"different"}}', content_type="application/json", **signed_headers()).status_code == 400
        assert fetch.call_count == 2
    with patch("payments.services.fetch_order", side_effect=MercadoPagoError("timeout")):
        assert client.post(url, "{}", content_type="application/json", **signed_headers()).status_code == 503


def test_webhook_no_debug_bypass_and_no_signature_only_from_body(client, credentials, settings):
    url = reverse("payments:mercadopago_webhook")
    assert client.get(url).status_code == 405
    assert client.post(url, '{"data":{"id":"ORDTest123"}}', content_type="application/json", **signed_headers()).status_code == 400
    settings.MERCADOPAGO_WEBHOOK_SECRET = ""
    assert client.post(url, "{}", content_type="application/json").status_code == 503


@pytest.mark.django_db
@pytest.mark.parametrize("failure", [requests.Timeout(), requests.ConnectionError()])
def test_checkout_uncertain_transport_keeps_reservation(order, credentials, failure):
    with patch("payments.mercadopago.requests.post", side_effect=failure):
        with pytest.raises(MercadoPagoUncertainError): create_checkout_order(order)
    assert order.items.get().product.stock == 3


def test_fetch_timeout_and_invalid_json_are_domain_errors(credentials):
    with patch("payments.mercadopago.requests.get", side_effect=requests.Timeout()):
        with pytest.raises(MercadoPagoError): fetch_order("ORDTest123")
    with patch("payments.mercadopago.requests.get", return_value=Mock(status_code=200, json=Mock(side_effect=ValueError))):
        with pytest.raises(MercadoPagoError): fetch_order("ORDTest123")
    with patch("payments.mercadopago.requests.get") as get:
        with pytest.raises(MercadoPagoError): fetch_order("../../bad")
        get.assert_not_called()


@pytest.mark.django_db
def test_return_url_never_marks_order_paid(client, order):
    result = client.get(reverse("order_confirmation", kwargs={"number": order.number, "result": "sucesso"}), {"status": "approved", "total": "0.01"})
    assert result.status_code == 200
    order.refresh_from_db()
    assert order.status == Order.Status.PENDING_PAYMENT


@pytest.mark.django_db
def test_processed_without_accredited_detail_does_not_confirm_payment(order):
    with patch("payments.services.fetch_order", return_value=remote(order, "processed", "unknown")):
        synchronize_mercadopago_order("ORDTest123")
    order.refresh_from_db()
    assert order.status == Order.Status.PENDING_PAYMENT


@pytest.mark.django_db
@pytest.mark.parametrize("status,data", [(503, {}), (201, {}), (201, {"id": "ORDTest123", "checkout_url": "https://attacker.example/"})])
def test_uncertain_creation_http_or_payload_never_claims_rejection(order, credentials, status, data):
    with patch("payments.mercadopago.requests.post", return_value=Mock(status_code=status, json=Mock(return_value=data))):
        with pytest.raises(MercadoPagoUncertainError): create_checkout_order(order)


@pytest.mark.django_db
def test_uncertain_checkout_view_preserves_order_and_stock_then_webhook_recovers(client, order, credentials):
    product = order.items.get().product
    data = {field: getattr(order, field) for field in (
        "customer_name", "customer_email", "customer_phone", "shipping_postal_code", "shipping_address",
        "shipping_number", "shipping_neighborhood", "shipping_city", "shipping_state")}
    url = reverse("orders:direct_checkout", kwargs={"product_id": product.pk, "quantity": 1})
    data["checkout_token"] = client.get(url).context["checkout_token"]
    with patch("orders.views.create_checkout_order", side_effect=MercadoPagoUncertainError("Pagamento em verificação")):
        result = client.post(url, data)
    uncertain = Order.objects.latest("created_at")
    assert result.status_code == 200
    assert uncertain.status == Order.Status.PENDING_PAYMENT and uncertain.provider_order_id == ""
    product.refresh_from_db()
    assert product.stock == 2
    with patch("payments.services.fetch_order", return_value=remote(uncertain)):
        synchronize_mercadopago_order("ORDTest123")
    uncertain.refresh_from_db()
    assert uncertain.status == Order.Status.PAID and uncertain.provider_order_id == "ORDTest123"
