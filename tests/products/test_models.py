from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError

from products.models import Category, Product


@pytest.mark.django_db
def test_category_string_representation():
    category = Category.objects.create(name="Painéis solares", slug="paineis-solares")

    assert str(category) == "Painéis solares"


@pytest.mark.django_db
def test_product_string_representation_and_defaults():
    category = Category.objects.create(name="Inversores", slug="inversores")
    product = Product.objects.create(
        category=category,
        name="Inversor solar",
        slug="inversor-solar",
        price=Decimal("2499.90"),
    )

    assert str(product) == "Inversor solar"
    assert product.stock == 0
    assert product.is_active is True
    assert product.product_type == Product.ProductType.PHYSICAL
    assert product.price == Decimal("2499.90")


@pytest.mark.django_db
def test_product_rejects_negative_price():
    category = Category.objects.create(name="Cabos", slug="cabos")
    product = Product(
        category=category,
        name="Cabo solar",
        slug="cabo-solar",
        price=Decimal("-1.00"),
    )

    with pytest.raises(ValidationError):
        product.full_clean()


@pytest.mark.django_db
def test_product_rejects_negative_stock():
    category = Category.objects.create(name="Baterias", slug="baterias")
    product = Product(
        category=category,
        name="Bateria solar",
        slug="bateria-solar",
        price=Decimal("100.00"),
        stock=-1,
    )

    with pytest.raises(ValidationError):
        product.full_clean()


@pytest.mark.django_db
def test_category_cannot_be_deleted_when_products_exist():
    category = Category.objects.create(name="Estruturas", slug="estruturas")
    Product.objects.create(
        category=category,
        name="Estrutura solar",
        slug="estrutura-solar",
        price=Decimal("100.00"),
    )

    with pytest.raises(ProtectedError):
        category.delete()
