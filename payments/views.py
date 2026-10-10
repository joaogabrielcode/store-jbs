import hashlib
import hmac
import json
import logging
import re

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .mercadopago import MercadoPagoError
from .services import synchronize_mercadopago_order

logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def mercadopago_webhook(request):
    secret = settings.MERCADOPAGO_WEBHOOK_SECRET
    if not secret:
        return HttpResponse(status=503)
    try:
        payload = json.loads(request.body or "{}")
        if not isinstance(payload, dict) or not isinstance(payload.get("data", {}), dict):
            raise ValueError
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=400)
    # The official signature authenticates data.id from the query string.
    provider_id = request.GET.get("data.id")
    if not provider_id or not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", provider_id):
        return HttpResponse(status=400)
    body_id = payload.get("data", {}).get("id")
    if body_id is not None and str(body_id) != provider_id:
        return HttpResponse(status=400)
    signature = request.headers.get("x-signature", "")
    request_id = request.headers.get("x-request-id", "")
    parts = dict(part.strip().split("=", 1) for part in signature.split(",") if "=" in part)
    timestamp, received_hash = parts.get("ts", ""), parts.get("v1", "")
    manifest = f"id:{provider_id};request-id:{request_id};ts:{timestamp};"
    expected_hash = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    if not request_id or not timestamp.isdigit() or not re.fullmatch(r"[a-fA-F0-9]{64}", received_hash) or not hmac.compare_digest(received_hash, expected_hash):
        logger.warning("Mercado Pago: assinatura inválida")
        return HttpResponse(status=403)
    topic = request.GET.get("type") or payload.get("type")
    if topic not in (None, "order"):
        return HttpResponse(status=200)
    try:
        order = synchronize_mercadopago_order(provider_id)
    except MercadoPagoError:
        logger.warning("Mercado Pago: sincronização não concluída")
        return HttpResponse(status=503)
    if order is None:
        return HttpResponse(status=503)
    return HttpResponse(status=200)
