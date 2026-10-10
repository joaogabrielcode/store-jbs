import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Aguardando pagamento"
        PAID = "paid", "Pago"
        PROCESSING = "processing", "Em preparação"
        SHIPPED = "shipped", "Enviado"
        DELIVERED = "delivered", "Entregue"
        CANCELED = "canceled", "Cancelado"
        REFUNDED = "refunded", "Reembolsado"

    class PaymentProvider(models.TextChoices):
        MERCADO_PAGO = "mercado_pago", "Mercado Pago"

    number = models.UUIDField("número", default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="usuário",
    )
    status = models.CharField(
        "status", max_length=24, choices=Status.choices, default=Status.PENDING_PAYMENT
    )
    payment_provider = models.CharField(
        "provedor de pagamento",
        max_length=24,
        choices=PaymentProvider.choices,
        default=PaymentProvider.MERCADO_PAGO,
    )
    provider_order_id = models.CharField("ID no provedor", max_length=120, blank=True)
    provider_status = models.CharField("status no provedor", max_length=60, blank=True)
    customer_name = models.CharField("nome do cliente", max_length=180)
    customer_email = models.EmailField("e-mail do cliente")
    customer_phone = models.CharField("telefone", max_length=30)
    shipping_postal_code = models.CharField("CEP", max_length=9)
    shipping_address = models.CharField("endereço", max_length=200)
    shipping_number = models.CharField("número", max_length=20)
    shipping_complement = models.CharField("complemento", max_length=120, blank=True)
    shipping_neighborhood = models.CharField("bairro", max_length=120)
    shipping_city = models.CharField("cidade", max_length=120)
    shipping_state = models.CharField("estado", max_length=2)
    subtotal = models.DecimalField("subtotal", max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(
        "frete", max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    total = models.DecimalField("total", max_digits=12, decimal_places=2)
    checkout_url = models.URLField("URL do checkout", blank=True)
    stock_released_at = models.DateTimeField("estoque liberado em", null=True, blank=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        constraints = [
            models.CheckConstraint(condition=Q(subtotal__gte=0), name="order_subtotal_non_negative"),
            models.CheckConstraint(condition=Q(shipping_cost__gte=0), name="order_shipping_non_negative"),
            models.CheckConstraint(condition=Q(total__gte=0), name="order_total_non_negative"),
        ]

    def __str__(self):
        return f"Pedido {self.number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="pedido")
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="produto",
    )
    product_name = models.CharField("nome do produto", max_length=180)
    unit_price = models.DecimalField("preço unitário", max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField("quantidade")
    subtotal = models.DecimalField("subtotal", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "item do pedido"
        verbose_name_plural = "itens do pedido"
        constraints = [
            models.CheckConstraint(condition=Q(unit_price__gte=0), name="order_item_unit_price_non_negative"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="order_item_quantity_positive"),
            models.CheckConstraint(condition=Q(subtotal__gte=0), name="order_item_subtotal_non_negative"),
        ]

    def __str__(self):
        return f"{self.product_name} ({self.quantity})"


class CheckoutAttempt(models.Model):
    """One server-issued form submission, shared by all of its retries."""

    token = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=40)
    checkout_path = models.CharField(max_length=250)
    items = models.JSONField()
    order = models.OneToOneField(
        Order, on_delete=models.PROTECT, null=True, blank=True,
        related_name="checkout_attempt",
    )
    created_at = models.DateTimeField(auto_now_add=True)
