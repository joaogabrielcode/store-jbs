from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Category(models.Model):
    name = models.CharField("nome", max_length=120)
    slug = models.SlugField("slug", max_length=140, unique=True)
    is_active = models.BooleanField("ativa", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "categoria"
        verbose_name_plural = "categorias"

    def __str__(self):
        return self.name


class Product(models.Model):
    class ProductType(models.TextChoices):
        PHYSICAL = "physical", "Produto físico"
        COURSE = "course", "Curso online"

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="categoria",
    )
    name = models.CharField("nome", max_length=180)
    slug = models.SlugField("slug", max_length=200, unique=True)
    description = models.TextField("descrição", blank=True)
    product_type = models.CharField(
        "tipo de produto",
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.PHYSICAL,
        db_default=ProductType.PHYSICAL,
    )
    price = models.DecimalField(
        "preço",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    stock = models.PositiveIntegerField("estoque", default=0)
    image_url = models.URLField("URL da imagem", blank=True)
    is_active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "produto"
        verbose_name_plural = "produtos"
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="product_price_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(stock__gte=0),
                name="product_stock_non_negative",
            ),
        ]

    def __str__(self):
        return self.name
