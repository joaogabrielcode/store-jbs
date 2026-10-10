from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from orders.models import Order
from payments.mercadopago import MercadoPagoError
from payments.services import expire_pending_order


class Command(BaseCommand):
    help = "Confere pedidos com mais de 24 horas e cancela apenas pagamentos não concluídos."

    def handle(self, *args, **options):
        pending = Order.objects.filter(
            status=Order.Status.PENDING_PAYMENT,
            payment_provider=Order.PaymentProvider.MERCADO_PAGO,
            created_at__lte=timezone.now() - timedelta(days=1),
        )
        canceled = errors = kept = 0
        for order in pending.iterator(chunk_size=100):
            try:
                updated = expire_pending_order(order)
            except MercadoPagoError as error:
                errors += 1
                self.stderr.write(f"Pedido {order.number}: {error}")
            else:
                if updated.status == Order.Status.CANCELED:
                    canceled += 1
                elif updated.status == Order.Status.PENDING_PAYMENT:
                    kept += 1
        self.stdout.write(f"Cancelados: {canceled}. Ainda pendentes: {kept}. Erros: {errors}.")
        if errors:
            raise CommandError("Há pedidos que precisam de nova consulta ou conciliação manual.")
