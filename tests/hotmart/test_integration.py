import json
from decimal import Decimal
from io import StringIO
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
import requests
from django.contrib.admin.sites import site
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse
from django.utils import timezone

from hotmart.client import HotmartClient, HotmartError
from hotmart.models import Course, WebhookEvent
from hotmart.services import sync_courses
from orders.models import Order


@pytest.fixture
def credentials(settings):
    settings.HOTMART_CLIENT_ID = "test-client"
    settings.HOTMART_CLIENT_SECRET = "test-secret"
    settings.HOTMART_BASIC_AUTH = "test-basic"
    settings.HOTMART_HOTTOK = "test-hottok"


@pytest.fixture
def product():
    return {"id": 1234567, "ucode": str(uuid4()), "name": "Curso solar", "status": "ACTIVE", "format": "ONLINE_COURSE", "is_subscription": False}


@pytest.fixture
def offer():
    return {"is_main_offer": True, "code": "test-offer", "price": {"value": "199.90", "currency_code": "BRL"}, "payment_mode": "PAY_IN_FULL", "direct_offer_link_for_creator": "https://pay.hotmart.com/A1234567A?off=test-offer"}


def response(data, status=200):
    return Mock(status_code=status, json=Mock(return_value=data))


def api_client(product, offer):
    return Mock(products=Mock(return_value=[product]), offers=Mock(return_value=[offer]))


@pytest.mark.django_db
def test_sync_command_paginates_products_and_offers_preserves_local_fields(credentials, product, offer):
    other = {**product, "id": 7654321, "ucode": str(uuid4()), "name": "Outro curso"}
    responses = [response({"access_token": "test-token"}),
                 response({"items": [product], "page_info": {"next_page_token": "products-next"}}),
                 response({"items": [], "page_info": {"next_page_token": "offers-next"}}),
                 response({"items": [offer], "page_info": {}}),
                 response({"items": [other], "page_info": {}}),
                 response({"items": [offer], "page_info": {}})]
    with patch("hotmart.client.requests.request", side_effect=responses) as request:
        out = StringIO()
        call_command("sync_hotmart_courses", stdout=out)
    assert "2 cursos" in out.getvalue()
    assert request.call_args_list[3].kwargs["params"]["page_token"] == "offers-next"
    assert request.call_args_list[4].kwargs["params"]["page_token"] == "products-next"
    assert request.call_args_list[1].kwargs["params"]["format"] == "ONLINE_COURSE"
    course = Course.objects.get(hotmart_id=product["id"])
    assert course.price == Decimal("199.90")
    assert course.checkout_url == offer["direct_offer_link_for_creator"]
    assert not course.is_visible
    course.slug = "slug-local"
    course.image = "https://example.com/course.png"
    course.short_description = "Texto local"
    course.description = "Descrição local"
    course.is_visible, course.is_featured, course.sort_order = True, True, 3
    course.save()
    product.update(name="Nome atualizado", status="PAUSED")
    offer["price"]["value"] = "250.00"
    sync_courses(api_client(product, offer))
    course.refresh_from_db()
    assert course.slug == "slug-local" and course.short_description == "Texto local"
    assert course.image == "https://example.com/course.png" and course.description == "Descrição local"
    assert course.is_visible and course.is_featured and course.sort_order == 3
    assert course.price == Decimal("250.00") and course.status == "PAUSED"
    assert Course.objects.get(hotmart_id=other["id"]).status == "UNAVAILABLE"
    assert Course.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize("invalid", ["negative", "nan", "currency", "url", "ucode", "precision"])
def test_bad_remote_data_never_partially_replaces_catalog(product, offer, invalid):
    sync_courses(api_client(product, offer))
    if invalid == "negative": offer["price"]["value"] = "-1"
    elif invalid == "nan": offer["price"]["value"] = "NaN"
    elif invalid == "currency": offer["price"]["currency_code"] = ""
    elif invalid == "url": offer["direct_offer_link_for_creator"] = "https://attacker.example/"
    elif invalid == "ucode": product["ucode"] = "broken"
    else: offer["price"]["value"] = "1.001"
    with pytest.raises(HotmartError): sync_courses(api_client(product, offer))
    assert Course.objects.get().price == Decimal("199.90")


@pytest.mark.django_db
def test_failed_pagination_leaves_existing_catalog_intact(product, offer):
    sync_courses(api_client(product, offer))
    def products():
        yield {**product, "name": "Mudou"}
        raise HotmartError("Falha na página seguinte")
    client = api_client(product, offer)
    client.products.return_value = products()
    with pytest.raises(HotmartError): sync_courses(client)
    assert Course.objects.get().name == "Curso solar"


@pytest.mark.parametrize("failure", [requests.Timeout(), requests.ConnectionError()])
def test_timeouts_are_sanitized(credentials, failure, caplog):
    with patch("hotmart.client.requests.request", side_effect=failure):
        with pytest.raises(HotmartError): HotmartClient().authenticate()
    assert "test-secret" not in caplog.text


def test_refreshes_token_once_on_401(credentials):
    with patch("hotmart.client.requests.request", side_effect=[
        response({"access_token": "old"}), response({}, 401), response({"access_token": "new"}),
        response({"items": [], "page_info": {}})]) as request:
        assert list(HotmartClient().products()) == []
    assert request.call_args.kwargs["headers"]["Authorization"] == "Bearer new"


@pytest.mark.parametrize("data", [{}, [], {"items": [], "page_info": None}])
def test_invalid_api_json(credentials, data):
    client = HotmartClient()
    client.access_token = "test-token"
    with patch("hotmart.client.requests.request", return_value=response(data)):
        with pytest.raises(HotmartError): list(client.products())


def test_repeated_cursor_is_rejected(credentials):
    client = HotmartClient()
    client.access_token = "test-token"
    with patch("hotmart.client.requests.request", return_value=response({"items": [], "page_info": {"next_page_token": "loop"}})):
        with pytest.raises(HotmartError): list(client.products())


def test_command_reports_missing_credentials(settings):
    settings.HOTMART_CLIENT_ID = ""
    with pytest.raises(CommandError): call_command("sync_hotmart_courses")


@pytest.mark.django_db
def test_courses_use_only_database_visibility_and_provider_availability(client, product, offer):
    sync_courses(api_client(product, offer))
    course = Course.objects.get()
    with patch("hotmart.client.requests.request") as api:
        content = client.get("/cursos/").content.decode()
        assert "Nenhum curso disponível" in content
        assert client.get(reverse("hotmart:course_detail", args=[course.slug])).status_code == 404
        course.is_visible = True
        course.save()
        content = client.get("/cursos/").content.decode()
        assert "Comprar na Hotmart" in content and "199,90" in content
        assert "https://pay.hotmart.com/" in content
        assert client.get(reverse("hotmart:course_detail", args=[course.slug])).status_code == 200
        course.status = "PAUSED"
        course.save()
        content = client.get("/cursos/").content.decode()
        assert "Compra indisponível" in content and "Comprar na Hotmart" not in content
        api.assert_not_called()
    assert not Order.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("subscription,has_offer,has_url", [(True, True, True), (False, False, True), (False, True, False)])
def test_missing_offer_url_or_subscription_never_invents_checkout(product, offer, subscription, has_offer, has_url):
    product["is_subscription"] = subscription
    if not has_url: offer.pop("direct_offer_link_for_creator")
    sync_courses(Mock(products=Mock(return_value=[product]), offers=Mock(return_value=[offer] if has_offer else [])))
    assert not Course.objects.get().can_purchase


@pytest.fixture
def event(product):
    return {"id": str(uuid4()), "event": "PURCHASE_APPROVED", "version": "2.0.0", "creation_date": 1700000000000,
            "data": {"product": {"id": product["id"]}, "purchase": {"transaction": "HPTEST123", "status": "APPROVED"},
                     "buyer": {"email": "private@example.com"}}}


@pytest.mark.django_db
def test_webhook_authenticated_idempotent_and_separate_from_orders(client, credentials, event):
    for _ in range(2):
        result = client.post("/webhooks/hotmart/", json.dumps(event), content_type="application/json", HTTP_X_HOTMART_HOTTOK="test-hottok")
        assert result.status_code == 200
    assert WebhookEvent.objects.count() == 1
    assert WebhookEvent.objects.get().purchase_status == "APPROVED"
    assert not Order.objects.exists() and not Course.objects.exists()
    assert "buyer" not in {f.name for f in WebhookEvent._meta.fields}


@pytest.mark.django_db
@pytest.mark.parametrize("payload", ["[]", "null", "{", '{"version":"1.0.0"}'])
def test_malformed_authenticated_webhook(client, credentials, payload):
    assert client.post("/webhooks/hotmart/", payload, content_type="application/json", HTTP_X_HOTMART_HOTTOK="test-hottok").status_code == 400
    assert not WebhookEvent.objects.exists()


def test_webhook_requires_post_and_secret_even_in_debug(client, settings, credentials, event):
    assert client.get("/webhooks/hotmart/").status_code == 405
    assert client.post("/webhooks/hotmart/", json.dumps(event), content_type="application/json").status_code == 403
    settings.HOTMART_HOTTOK = ""
    assert client.post("/webhooks/hotmart/", "{}", content_type="application/json").status_code == 503


@pytest.mark.django_db
def test_admin_provider_fields_readonly_and_local_fields_editable(client, django_user_model, product, offer):
    sync_courses(api_client(product, offer))
    course = Course.objects.get()
    user = django_user_model.objects.create_superuser(username="admin-test", email="admin@example.com", password="test-password")
    client.force_login(user)
    content = client.get(reverse("admin:hotmart_course_change", args=[course.pk])).content.decode()
    assert 'name="slug"' in content and 'name="is_visible"' in content
    assert 'name="price"' not in content and 'name="checkout_url"' not in content
    assert "/static/css/main.css" not in content
    assert not site._registry[Course].has_add_permission(Mock(user=user))


@pytest.mark.django_db
def test_identifier_conflict_rolls_back_all_updates(product, offer):
    sync_courses(api_client(product, offer))
    other = {**product, "id": 7654321, "name": "ID duplicado para o mesmo ucode"}
    with pytest.raises(HotmartError):
        sync_courses(Mock(products=Mock(return_value=[{**product, "name": "Novo nome"}, other]),
                          offers=Mock(return_value=[offer])))
    assert Course.objects.count() == 1
    assert Course.objects.get().name == "Curso solar"


@pytest.mark.parametrize("status", [403, 429, 500])
def test_remote_http_errors_and_bad_json_are_sanitized(credentials, status):
    client = HotmartClient()
    client.access_token = "test-token"
    with patch("hotmart.client.requests.request", return_value=response({"secret": "do-not-log"}, status)):
        with pytest.raises(HotmartError, match=f"HTTP {status}"):
            list(client.products())
    with patch("hotmart.client.requests.request", return_value=Mock(status_code=200, json=Mock(side_effect=ValueError))):
        with pytest.raises(HotmartError, match="JSON inválido"):
            list(client.products())


@pytest.mark.django_db
def test_only_main_offer_price_is_used_and_discount_offer_is_ignored(product, offer):
    promotional = {**offer, "is_main_offer": False, "code": "promotion", "price": {"value": "49.90", "currency_code": "BRL"},
                   "direct_offer_link_for_creator": "https://pay.hotmart.com/A1234567A?off=promotion"}
    sync_courses(Mock(products=Mock(return_value=[product]), offers=Mock(return_value=[promotional, offer])))
    course = Course.objects.get()
    assert course.offer_code == "test-offer"
    assert course.price == Decimal("199.90")
    assert "promotion" not in course.checkout_url
