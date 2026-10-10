from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier, Event
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.db import connections
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone

from orders.models import CheckoutAttempt, Order
from orders.services import claim_checkout_attempt
from payments.mercadopago import MercadoPagoError, MercadoPagoUncertainError
from products.models import Category, Product


@pytest.fixture
def product(db):
    category = Category.objects.create(name="Painéis", slug="tentativa-paineis")
    return Product.objects.create(category=category, name="Painel", slug="tentativa-painel", price=Decimal("100.00"), stock=5)


def customer_data():
    return {
        "customer_name": "Cliente", "customer_email": "cliente@example.com",
        "customer_phone": "11999999999", "shipping_postal_code": "01001-000",
        "shipping_address": "Praça da Sé", "shipping_number": "1",
        "shipping_complement": "", "shipping_neighborhood": "Sé",
        "shipping_city": "São Paulo", "shipping_state": "SP",
    }


def open_checkout(client, product, cart=False, quantity=2):
    if cart:
        client.post(reverse("orders:cart_add", args=[product.pk]), {"quantity": quantity})
        url = reverse("orders:checkout")
    else:
        url = reverse("orders:direct_checkout", args=[product.pk, quantity])
    page = client.get(url)
    return url, {**customer_data(), "checkout_token": page.context["checkout_token"]}


def provider_result():
    return {"id": "ORDRepeat123", "checkout_url": "https://www.mercadopago.com.br/checkout/test"}


@pytest.mark.django_db
@pytest.mark.parametrize("cart", [False, True])
def test_repeated_posts_reuse_order_reservation_and_provider_checkout(client, product, cart):
    url, data = open_checkout(client, product, cart)
    with patch("orders.views.create_checkout_order", return_value=provider_result()) as create:
        first = client.post(url, data)
        second = client.post(url, {**data, "customer_email": "changed@example.com", "total": "0.01"})
    assert first.status_code == second.status_code == 302
    assert first.url == second.url == provider_result()["checkout_url"]
    assert Order.objects.count() == 1
    assert Order.objects.get().customer_email == "cliente@example.com"
    product.refresh_from_db()
    assert product.stock == 3
    assert create.call_count == 1
    if cart:
        assert client.session["cart"] == {}


@pytest.mark.django_db
def test_replay_works_when_first_purchase_exhausted_stock(client, product):
    url, data = open_checkout(client, product, quantity=5)
    with patch("orders.views.create_checkout_order", return_value=provider_result()) as create:
        assert client.post(url, data).status_code == 302
        assert client.post(url, data).url == provider_result()["checkout_url"]
    assert create.call_count == 1
    product.refresh_from_db()
    assert product.stock == 0


@pytest.mark.django_db
@pytest.mark.parametrize("problem", ["missing", "invalid", "unknown", "other_session", "other_path"])
def test_token_requires_server_issuance_same_session_and_same_purchase(client, product, problem):
    url, data = open_checkout(client, product)
    if problem == "missing": data.pop("checkout_token")
    elif problem == "invalid": data["checkout_token"] = "bad"
    elif problem == "unknown": data["checkout_token"] = str(uuid4())
    elif problem == "other_session": client = Client()
    else: url = reverse("orders:direct_checkout", args=[product.pk, 3])
    with patch("orders.views.create_checkout_order") as create:
        result = client.post(url, data)
    assert result.status_code == 400
    assert not Order.objects.exists()
    create.assert_not_called()


@pytest.mark.django_db
def test_changed_cart_requires_fresh_checkout(client, product):
    url, data = open_checkout(client, product, cart=True)
    client.post(reverse("orders:cart_update", args=[product.pk]), {"quantity": 3})
    with patch("orders.views.create_checkout_order") as create:
        result = client.post(url, data)
    assert result.status_code == 200 and "O carrinho mudou" in result.content.decode()
    assert not Order.objects.exists()
    create.assert_not_called()


@pytest.mark.django_db
def test_expired_unused_attempt_cannot_reserve_stock(client, product):
    url, data = open_checkout(client, product)
    CheckoutAttempt.objects.filter(pk=data["checkout_token"]).update(created_at=timezone.now() - timedelta(days=1))
    with patch("orders.views.create_checkout_order") as create:
        result = client.post(url, data)
    assert result.status_code == 200 and "tentativa expirou" in result.content.decode()
    assert not Order.objects.exists()
    create.assert_not_called()


@pytest.mark.django_db
def test_uncertain_response_is_not_a_new_order_on_resubmit(client, product):
    url, data = open_checkout(client, product)
    with patch("orders.views.create_checkout_order", side_effect=MercadoPagoUncertainError("Pagamento em verificação")) as create:
        assert client.post(url, data).status_code == 200
        result = client.post(url, data)
    assert result.status_code == 302 and "/pedidos/" in result.url
    assert Order.objects.count() == 1
    assert create.call_count == 1
    product.refresh_from_db()
    assert product.stock == 3


@pytest.mark.django_db
def test_explicit_rejection_consumes_old_token_and_allows_fresh_attempt(client, product):
    url, data = open_checkout(client, product)
    with patch("orders.views.create_checkout_order", side_effect=MercadoPagoError("Recusado")) as create:
        result = client.post(url, data)
        fresh = result.context["checkout_token"]
        replay = client.post(url, data)
    assert fresh != data["checkout_token"]
    assert replay.status_code == 302 and "/pedidos/" in replay.url
    assert create.call_count == 1 and Order.objects.count() == 1
    with patch("orders.views.create_checkout_order", return_value=provider_result()):
        assert client.post(url, {**data, "checkout_token": fresh}).status_code == 302
    assert Order.objects.count() == 2
    product.refresh_from_db()
    assert product.stock == 3


@pytest.mark.django_db
def test_new_form_can_start_another_intentional_purchase(client, product):
    with patch("orders.views.create_checkout_order", return_value=provider_result()) as create:
        first_url, first_data = open_checkout(client, product, quantity=1)
        client.post(first_url, first_data)
        second_url, second_data = open_checkout(client, product, quantity=1)
        client.post(second_url, second_data)
    assert first_data["checkout_token"] != second_data["checkout_token"]
    assert Order.objects.count() == create.call_count == 2


@pytest.mark.django_db
def test_paid_or_overdue_replay_shows_local_order_without_new_payment(client, product):
    url, data = open_checkout(client, product)
    with patch("orders.views.create_checkout_order", return_value=provider_result()) as create:
        client.post(url, data)
        order = Order.objects.get()
        Order.objects.filter(pk=order.pk).update(created_at=timezone.now() - timedelta(days=1))
        assert "/pedidos/" in client.post(url, data).url
        Order.objects.filter(pk=order.pk).update(status=Order.Status.PAID)
        assert "/pedidos/" in client.post(url, data).url
    assert create.call_count == 1


@pytest.mark.django_db(transaction=True)
def test_parallel_claims_commit_one_order_and_one_stock_reservation(client, product):
    url, data = open_checkout(client, product)
    attempt = CheckoutAttempt.objects.get(pk=data["checkout_token"])
    session_key = client.session.session_key
    barrier = Barrier(2)

    def claim():
        try:
            request = RequestFactory().post(url)
            request.session = SessionStore(session_key=session_key)
            request.user = AnonymousUser()
            barrier.wait(timeout=10)
            order, created = claim_checkout_attempt(request, attempt, customer_data(), direct_purchase=True)
            return order.pk, created
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(pool.map(lambda _: claim(), range(2)))
    assert first[0] == second[0]
    assert sorted([first[1], second[1]]) == [False, True]
    assert Order.objects.count() == 1
    product.refresh_from_db()
    assert product.stock == 3


@pytest.mark.django_db(transaction=True)
def test_second_http_post_during_provider_call_does_not_call_provider_again(client, product):
    url, data = open_checkout(client, product)
    cookies = client.cookies.copy()
    started, release = Event(), Event()

    def provider(order):
        started.set()
        assert release.wait(timeout=10)
        return provider_result()

    def post():
        try:
            worker = Client()
            worker.cookies = cookies.copy()
            return worker.post(url, data)
        finally:
            connections.close_all()

    with patch("orders.views.create_checkout_order", side_effect=provider) as create:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(post)
            assert started.wait(timeout=10)
            try:
                second = pool.submit(post).result(timeout=10)
                assert second.status_code == 302 and "/pedidos/" in second.url
            finally:
                release.set()
            assert first.result(timeout=10).url == provider_result()["checkout_url"]
    assert create.call_count == 1
    assert Order.objects.count() == 1
