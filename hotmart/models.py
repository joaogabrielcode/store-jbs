from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Course(models.Model):
    hotmart_id = models.PositiveBigIntegerField("ID Hotmart", unique=True)
    hotmart_ucode = models.UUIDField("ucode Hotmart", unique=True)
    name = models.CharField("nome", max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    status = models.CharField("status Hotmart", max_length=60)
    offer_code = models.CharField("oferta", max_length=120, blank=True)
    checkout_url = models.URLField("checkout Hotmart", max_length=1000, blank=True)
    price = models.DecimalField(
        "preço", max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField("moeda", max_length=3, blank=True)
    image = models.URLField("URL da imagem de apresentação", max_length=1000, blank=True)
    short_description = models.CharField("descrição curta", max_length=300, blank=True)
    description = models.TextField("descrição comercial", blank=True)
    is_visible = models.BooleanField("visível na loja", default=False)
    is_featured = models.BooleanField("destaque", default=False)
    sort_order = models.PositiveIntegerField("ordem", default=0)
    last_synced_at = models.DateTimeField("sincronizado em")

    class Meta:
        ordering = ["-is_featured", "sort_order", "name"]
        verbose_name = "curso Hotmart"
        verbose_name_plural = "cursos Hotmart"
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=0) | Q(price__isnull=True),
                name="hotmart_course_price_non_negative",
            )
        ]

    @property
    def can_purchase(self):
        return (
            self.status == "ACTIVE"
            and bool(self.checkout_url and self.offer_code and self.currency)
            and self.price is not None
        )

    def __str__(self):
        return self.name


class WebhookEvent(models.Model):
    """Minimal authenticated receipt; purchases are fulfilled by Hotmart."""

    event_id = models.CharField("ID do evento", max_length=120, unique=True)
    event = models.CharField("evento", max_length=120)
    hotmart_id = models.PositiveBigIntegerField("ID do produto")
    transaction = models.CharField("transação", max_length=120, blank=True)
    purchase_status = models.CharField("status da compra", max_length=60, blank=True)
    creation_date = models.PositiveBigIntegerField("data do evento (ms)")
    received_at = models.DateTimeField("recebido em", auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "evento Hotmart"
        verbose_name_plural = "eventos Hotmart"
