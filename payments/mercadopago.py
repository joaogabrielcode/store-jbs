import logging
import re
import uuid
from urllib.parse import urlparse

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class MercadoPagoError(Exception):
    pass


class MercadoPagoNotConfigured(MercadoPagoError):
    pass


class MercadoPagoUncertainError(MercadoPagoError):
    """The provider may have accepted the order; keep stock reserved."""


def create_checkout_order(order):
    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        raise MercadoPagoNotConfigured("MERCADOPAGO_ACCESS_TOKEN não configurado.")

    site = urlparse(settings.SITE_URL)
    if not site.netloc or site.scheme not in ({"http", "https"} if settings.DEBUG else {"https"}):
        raise MercadoPagoNotConfigured("Configure SITE_URL com a URL pública da loja.")
    if order.total != sum(item.unit_price * item.quantity for item in order.items.all()):
        raise MercadoPagoError("O total do pedido diverge dos itens de pagamento.")

    items = [
        {
            "title": item.product_name,
            "quantity": item.quantity,
            "unit_price": f"{item.unit_price:.2f}",
            "total_amount": f"{item.subtotal:.2f}",
            "unit_measure": "unit",
        }
        for item in order.items.all()
    ]
    payload = {
        "type": "online",
        "processing_mode": "manual",
        "capture_mode": "automatic_async",
        "expiration_time": "P1D",
        "total_amount": f"{order.total:.2f}",
        "external_reference": str(order.number),
        "payer": {"email": order.customer_email},
        "items": items,
        "config": {
            "redirect_urls": {
                "success": f"{settings.SITE_URL}/pedidos/{order.number}/sucesso/",
                "failure": f"{settings.SITE_URL}/pedidos/{order.number}/falha/",
                "pending": f"{settings.SITE_URL}/pedidos/{order.number}/pendente/",
            }
        },
    }
    try:
        response = requests.post(
            f"{settings.MERCADOPAGO_API_URL}/v1/orders",
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Idempotency-Key": str(order.number),
            },
            timeout=15,
            allow_redirects=False,
        )
    except requests.RequestException:
        logger.warning("Mercado Pago: criação inconclusiva para pedido %s", order.number)
        raise MercadoPagoUncertainError("Pagamento em verificação. Aguarde a confirmação antes de comprar novamente.") from None
    if response.status_code >= 500:
        raise MercadoPagoUncertainError("Pagamento em verificação. Aguarde a confirmação antes de comprar novamente.")
    if not 200 <= response.status_code < 300:
        logger.warning("Mercado Pago: criação recusada HTTP %s", response.status_code)
        raise MercadoPagoError("Mercado Pago não aceitou a ordem de pagamento.")
    try:
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError
    except ValueError:
        raise MercadoPagoUncertainError("Mercado Pago retornou uma resposta inválida; pagamento em verificação.") from None
    if not data.get("id") or not data.get("checkout_url"):
        raise MercadoPagoUncertainError("Mercado Pago retornou uma resposta incompleta; pagamento em verificação.")
    if not isinstance(data["id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", data["id"]) or not isinstance(data["checkout_url"], str):
        raise MercadoPagoUncertainError("Mercado Pago retornou identificador ou checkout inválido.")
    parsed = urlparse(data["checkout_url"])
    if parsed.scheme != "https" or parsed.hostname not in {"www.mercadopago.com.br", "mercadopago.com.br"} or parsed.username or parsed.password:
        raise MercadoPagoUncertainError("Mercado Pago retornou uma URL de checkout inválida.")
    return data


def fetch_order(provider_order_id):
    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        raise MercadoPagoNotConfigured("MERCADOPAGO_ACCESS_TOKEN não configurado.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", str(provider_order_id)):
        raise MercadoPagoError("ID de pagamento inválido.")
    try:
        response = requests.get(
            f"{settings.MERCADOPAGO_API_URL}/v1/orders/{provider_order_id}",
            headers={"Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"},
            timeout=15,
            allow_redirects=False,
        )
    except requests.RequestException:
        logger.warning("Mercado Pago: consulta indisponível")
        raise MercadoPagoError("Não foi possível consultar o Mercado Pago.") from None
    if not 200 <= response.status_code < 300:
        logger.warning("Mercado Pago: consulta HTTP %s", response.status_code)
        raise MercadoPagoError("Não foi possível consultar a ordem no Mercado Pago.")
    try:
        data = response.json()
    except ValueError:
        raise MercadoPagoError("Mercado Pago retornou JSON inválido.") from None
    if not isinstance(data, dict):
        raise MercadoPagoError("Mercado Pago retornou uma resposta inválida.")
    return data


def cancel_provider_order(order):
    """Cancel an unpaid remote order; confirmation is fetched separately."""
    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        raise MercadoPagoNotConfigured("MERCADOPAGO_ACCESS_TOKEN não configurado.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", order.provider_order_id):
        raise MercadoPagoError("ID de pagamento inválido.")
    try:
        response = requests.post(
            f"{settings.MERCADOPAGO_API_URL}/v1/orders/{order.provider_order_id}/cancel",
            headers={
                "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Idempotency-Key": str(uuid.uuid5(order.number, "cancel-expired-order")),
            },
            timeout=15, allow_redirects=False,
        )
    except requests.RequestException:
        raise MercadoPagoError("Cancelamento não confirmado pelo Mercado Pago.") from None
    # A 409 can mean an intervening payment or a previous cancellation; always refetch.
    if not 200 <= response.status_code < 300 and response.status_code != 409:
        logger.warning("Mercado Pago: cancelamento HTTP %s", response.status_code)
        raise MercadoPagoError("Cancelamento não confirmado pelo Mercado Pago.")
