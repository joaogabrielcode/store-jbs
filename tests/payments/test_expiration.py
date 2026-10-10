from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import Mock, patch

import pytest
import requests
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from orders.models import Order
from orders.services import create_order
from payments.mercadopago import MercadoPagoError, cancel_provider_order
from payments.services import expire_pending_order
from products.models import Category, Product


@pytest.fixture
def overdue_order(client, db):
    category = Category.objects.create(name="Painéis", slug="expiracao-paineis")
    product = Product.objects.create(category=category, name="Painel", slug="expiracao-painel", price=Decimal("100.00"), stock=3)
    order = create_order(client, {
        "customer_name": "Cliente", "customer_email": "cliente@example.com", "customer_phone": "11999999999",
        "shipping_postal_code": "01001-000", "shipping_address": "Praça da Sé", "shipping_number": "1",
        "shipping_neighborhood": "Sé", "shipping_city": "São Paulo", "shipping_state": "SP",
    }, {product.pk: 2})
    Order.objects.filter(pk=order.pk).update(created_at=timezone.now() - timedelta(days=1, minutes=1), provider_order_id="ORDExpire123")
    order.refresh_from_db()
    return order


def remote(order, status="created", detail="created"):
    return {"id": "ORDExpire123", "external_reference": str(order.number), "total_amount": str(order.total),
            "status": status, "status_detail": detail}


@pytest.mark.django_db
def test_overdue_created_order_is_cancelled_remotely_before_stock_release(overdue_order):
    with patch("payments.services.fetch_order", side_effect=[remote(overdue_order), remote(overdue_order, "canceled", "canceled")]) as fetch:
        with patch("payments.services.cancel_provider_order") as cancel:
            result = expire_pending_order(overdue_order)
    assert result.status == Order.Status.CANCELED
    assert cancel.call_count == 1 and fetch.call_count == 2
    assert overdue_order.items.get().product.stock == 3
    with patch("payments.services.fetch_order") as fetch:
        expire_pending_order(overdue_order)
        fetch.assert_not_called()
    assert overdue_order.items.get().product.stock == 3


@pytest.mark.django_db
@pytest.mark.parametrize("status,detail,expected", [
    ("processed", "accredited", Order.Status.PAID),
    ("processing", "in_process", Order.Status.PENDING_PAYMENT),
    ("processed", "partially_refunded", Order.Status.PAID),
    ("refunded", "refunded", Order.Status.REFUNDED),
])
def test_paid_or_processing_order_keeps_reserved_goods(overdue_order, status, detail, expected):
    with patch("payments.services.fetch_order", return_value=remote(overdue_order, status, detail)):
        with patch("payments.services.cancel_provider_order") as cancel:
            result = expire_pending_order(overdue_order)
    assert result.status == expected
    assert overdue_order.items.get().product.stock == 1
    cancel.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("problem", ["lookup", "cancel_timeout", "still_created", "payment_won_race", "different_total", "missing_id"])
def test_expiration_never_releases_stock_without_provider_confirmation(overdue_order, problem):
    data = remote(overdue_order)
    if problem == "different_total": data["total_amount"] = "0.01"
    if problem == "missing_id":
        overdue_order.provider_order_id = ""
        overdue_order.save()
    second = remote(overdue_order, "processed", "accredited") if problem == "payment_won_race" else data
    with patch("payments.services.fetch_order", side_effect=MercadoPagoError("consulta indisponível") if problem == "lookup" else [data, second]):
        with patch("payments.services.cancel_provider_order", side_effect=MercadoPagoError("timeout") if problem == "cancel_timeout" else None):
            if problem in {"lookup", "cancel_timeout", "different_total", "missing_id"}:
                with pytest.raises(MercadoPagoError): expire_pending_order(overdue_order)
            else:
                expire_pending_order(overdue_order)
    overdue_order.refresh_from_db()
    assert overdue_order.status == (Order.Status.PAID if problem == "payment_won_race" else Order.Status.PENDING_PAYMENT)
    assert overdue_order.stock_released_at is None
    assert overdue_order.items.get().product.stock == 1


@pytest.mark.django_db
def test_unexpired_orders_are_not_queried(overdue_order):
    Order.objects.filter(pk=overdue_order.pk).update(created_at=timezone.now() - timedelta(hours=23))
    with patch("payments.services.fetch_order") as fetch:
        expire_pending_order(overdue_order)
        fetch.assert_not_called()


@pytest.mark.django_db
def test_remote_cancel_uses_stable_distinct_idempotency_key(overdue_order, settings):
    settings.MERCADOPAGO_ACCESS_TOKEN = "test-token"
    with patch("payments.mercadopago.requests.post", return_value=Mock(status_code=200)) as post:
        cancel_provider_order(overdue_order)
        cancel_provider_order(overdue_order)
    first, second = post.call_args_list
    assert first.args[0].endswith("/v1/orders/ORDExpire123/cancel")
    key = first.kwargs["headers"]["X-Idempotency-Key"]
    assert key == second.kwargs["headers"]["X-Idempotency-Key"]
    assert key != str(overdue_order.number)
    assert not first.kwargs["allow_redirects"]


@pytest.mark.django_db
@pytest.mark.parametrize("failure", [requests.Timeout(), requests.ConnectionError()])
def test_remote_cancel_transport_error_is_sanitized(overdue_order, settings, failure):
    settings.MERCADOPAGO_ACCESS_TOKEN = "test-token"
    with patch("payments.mercadopago.requests.post", side_effect=failure):
        with pytest.raises(MercadoPagoError): cancel_provider_order(overdue_order)


@pytest.mark.django_db
def test_remote_cancel_409_is_followed_by_authoritative_refetch(overdue_order, settings):
    settings.MERCADOPAGO_ACCESS_TOKEN = "test-token"
    with patch("payments.mercadopago.requests.post", return_value=Mock(status_code=409)):
        with patch("payments.services.fetch_order", side_effect=[remote(overdue_order), remote(overdue_order, "processed", "accredited")]) as fetch:
            result = expire_pending_order(overdue_order)
    assert result.status == Order.Status.PAID and fetch.call_count == 2
    assert overdue_order.items.get().product.stock == 1


@pytest.mark.django_db
def test_command_reports_errors_and_continues_other_orders(overdue_order):
    other = Order.objects.create(
        customer_name="Outro", customer_email="outro@example.com", customer_phone="11999999999",
        shipping_postal_code="01001-000", shipping_address="Praça da Sé", shipping_number="1",
        shipping_neighborhood="Sé", shipping_city="São Paulo", shipping_state="SP",
        subtotal=100, total=100, provider_order_id="ORDOther123",
    )
    Order.objects.filter(pk=other.pk).update(created_at=timezone.now() - timedelta(days=2))
    out, err = StringIO(), StringIO()
    def expire(order):
        if order.pk == overdue_order.pk:
            raise MercadoPagoError("Consulta falhou")
        order.status = Order.Status.CANCELED
        return order
    with patch("orders.management.commands.expire_pending_orders.expire_pending_order", side_effect=expire) as service:
        with pytest.raises(CommandError):
            call_command("expire_pending_orders", stdout=out, stderr=err)
    assert service.call_count == 2
    assert "Cancelados: 1" in out.getvalue() and "Erros: 1" in out.getvalue()
    assert str(overdue_order.number) in err.getvalue()
