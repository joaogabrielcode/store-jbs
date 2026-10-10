import logging
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
from uuid import UUID

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from .client import HotmartClient, HotmartError
from .models import Course, WebhookEvent

logger = logging.getLogger(__name__)


def course_data(product, offers):
    try:
        product_id = int(product["id"])
        ucode = UUID(str(product["ucode"]))
        name, status = product["name"], product["status"]
        if (
            not 0 < product_id <= 9223372036854775807
            or not isinstance(name, str) or not name or len(name) > 255
            or not isinstance(status, str) or not status or len(status) > 60
        ):
            raise ValueError
        main = [offer for offer in offers if offer.get("is_main_offer") is True]
        if len(main) > 1:
            raise ValueError
        data = {
            "hotmart_ucode": ucode, "name": name, "status": status,
            "offer_code": "", "checkout_url": "", "price": None, "currency": "",
        }
        # Subscription plans require a different price presentation; leave them unavailable.
        if main and not product.get("is_subscription") and main[0].get("payment_mode") == "PAY_IN_FULL":
            offer = main[0]
            price = Decimal(str(offer["price"]["value"]))
            currency = offer["price"]["currency_code"]
            url = offer.get("direct_offer_link_for_creator", "")
            code = offer["code"]
            if (
                not price.is_finite() or price < 0 or price >= Decimal("10000000000")
                or price != price.quantize(Decimal("0.01"))
            ):
                raise ValueError
            if (
                not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha()
                or not isinstance(code, str) or not code or len(code) > 120
            ):
                raise ValueError
            if url:
                URLValidator(schemes=["https"])(url)
                parsed = urlparse(url)
                if (
                    parsed.hostname != "pay.hotmart.com" or parsed.username or parsed.password
                    or parsed.port not in (None, 443) or len(url) > 1000
                ):
                    raise ValueError
            data.update(offer_code=code, checkout_url=url, price=price, currency=currency.upper())
        return product_id, data
    except (KeyError, TypeError, ValueError, InvalidOperation, ValidationError):
        raise HotmartError("Hotmart retornou dados inválidos de produto ou oferta.") from None


def sync_courses(client=None):
    client = client or HotmartClient()
    rows = {}
    for product in client.products():
        if product.get("format") != "ONLINE_COURSE":
            continue
        product_id, data = course_data(product, list(client.offers(product.get("ucode", ""))))
        rows[product_id] = data
    # No catalog changes until every remote page and offer has been validated.
    now = timezone.now()
    try:
        with transaction.atomic():
            for product_id, data in rows.items():
                data["last_synced_at"] = now
                Course.objects.update_or_create(
                    hotmart_id=product_id,
                    defaults=data,
                    create_defaults={
                        **data,
                        "slug": f"{slugify(data['name'])[:240] or 'curso'}-{product_id}",
                    },
                )
            Course.objects.exclude(hotmart_id__in=rows).update(
                status="UNAVAILABLE", checkout_url="", last_synced_at=now
            )
    except IntegrityError:
        raise HotmartError("Conflito de identificadores ou slug na sincronização Hotmart.") from None
    logger.info("Hotmart: %s cursos sincronizados", len(rows))
    return len(rows)


@transaction.atomic
def process_webhook(payload):
    """Record purchase events once, without changing course or physical order state."""
    try:
        event_id, event = payload["id"], payload["event"]
        if payload.get("version") != "2.0.0":
            raise ValueError
        if not all(isinstance(value, str) and 0 < len(value) <= 120 for value in (event_id, event)):
            raise ValueError
        data = payload["data"]
        product_id = int(data["product"]["id"])
        created = int(payload["creation_date"])
        if not 0 < product_id <= 9223372036854775807 or not 0 <= created <= 9223372036854775807:
            raise ValueError
        purchase = data.get("purchase", {})
        transaction_id, status = purchase.get("transaction", ""), purchase.get("status", "")
        if (
            not isinstance(transaction_id, str) or len(transaction_id) > 120
            or not isinstance(status, str) or len(status) > 60
        ):
            raise ValueError
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ValueError("Evento Hotmart inválido.") from None
    _, created = WebhookEvent.objects.get_or_create(
        event_id=event_id,
        defaults={
            "event": event, "hotmart_id": product_id, "transaction": transaction_id,
            "purchase_status": status, "creation_date": created,
        },
    )
    logger.info("Hotmart: evento recebido, novo=%s", created)
    return created
