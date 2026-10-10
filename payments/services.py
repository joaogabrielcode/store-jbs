import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from orders.models import Order
from orders.services import cancel_order, mark_order_as_paid
from .mercadopago import MercadoPagoError, cancel_provider_order, fetch_order

logger = logging.getLogger(__name__)


def synchronize_mercadopago_order(provider_order_id):
    provider_order = fetch_order(provider_order_id)
    return _apply_mercadopago_status(provider_order_id, provider_order)


@transaction.atomic
def _apply_mercadopago_status(provider_order_id, provider_order):
    try:
        reference = UUID(str(provider_order["external_reference"]))
        amount = Decimal(str(provider_order["total_amount"]))
        if str(provider_order["id"]) != str(provider_order_id) or not amount.is_finite():
            raise ValueError
    except (KeyError, TypeError, ValueError, InvalidOperation):
        raise MercadoPagoError("Resposta do Mercado Pago sem referência ou valor válido.") from None
    try:
        order = Order.objects.select_for_update().get(number=reference, payment_provider=Order.PaymentProvider.MERCADO_PAGO)
    except Order.DoesNotExist:
        logger.warning("Mercado Pago: pedido local não encontrado")
        return None
    if amount != order.total or (order.provider_order_id and order.provider_order_id != str(provider_order_id)):
        logger.warning("Mercado Pago: referência, ID ou valor divergente para pedido %s", order.number)
        raise MercadoPagoError("Pagamento diverge do pedido local.")
    status = provider_order.get("status", "")
    detail = provider_order.get("status_detail", "")
    if not isinstance(status, str) or not status or not isinstance(detail, str) or len(f"{status}:{detail}") > 60:
        raise MercadoPagoError("Status inválido do Mercado Pago.")
    # Full refunds never automatically return shipped goods to stock.
    if status == "refunded" or (status == "processed" and detail == "refunded"):
        order.status = Order.Status.REFUNDED
    elif status == "processed" and detail in {"accredited", "partially_refunded"}:
        if order.status == Order.Status.PENDING_PAYMENT:
            order = mark_order_as_paid(order)
        elif order.status in {Order.Status.CANCELED, Order.Status.REFUNDED}:
            logger.error("Mercado Pago: pagamento após encerramento do pedido %s; requer conciliação", order.number)
            raise MercadoPagoError("Pagamento requer conciliação manual do pedido encerrado.")
    elif status in {"expired", "canceled", "failed"}:
        if order.status == Order.Status.PENDING_PAYMENT:
            order = cancel_order(order)
    order.provider_order_id = str(provider_order["id"])
    order.provider_status = f"{status}:{detail}" if detail else status
    order.save(update_fields=["status", "provider_order_id", "provider_status", "updated_at"])
    logger.info("Mercado Pago: pedido %s, status %s", order.number, order.provider_status)
    return order


def expire_pending_order(order):
    """Release stock only after authoritative cancellation of an overdue order."""
    order.refresh_from_db()
    if order.status != Order.Status.PENDING_PAYMENT or order.created_at > timezone.now() - timedelta(days=1):
        return order
    if not order.provider_order_id:
        raise MercadoPagoError("Pedido sem ID remoto requer conciliação manual.")
    synchronized = synchronize_mercadopago_order(order.provider_order_id)
    if synchronized is None:
        raise MercadoPagoError("Pedido não localizado durante a conciliação.")
    if synchronized.status != Order.Status.PENDING_PAYMENT:
        return synchronized
    if synchronized.provider_status.split(":", 1)[0] in {"created", "action_required"}:
        cancel_provider_order(synchronized)
        synchronized = synchronize_mercadopago_order(synchronized.provider_order_id)
        if synchronized is None:
            raise MercadoPagoError("Cancelamento requer conciliação.")
    return synchronized
