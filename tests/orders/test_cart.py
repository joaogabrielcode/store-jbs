from decimal import Decimal

import pytest
from django.urls import reverse

from products.models import Category, Product


@pytest.fixture
def product(db):
    category = Category.objects.create(name="Painéis", slug="paineis")
    return Product.objects.create(
        category=category,
        name="Painel solar 550W",
        slug="painel-solar-550w",
        price=Decimal("899.90"),
        stock=5,
    )


@pytest.mark.django_db
def test_add_product_to_session_cart(client, product):
    response = client.post(
        reverse("orders:cart_add", kwargs={"product_id": product.id}),
        {"quantity": 2},
    )

    assert response.status_code == 302
    assert client.session["cart"] == {str(product.id): 2}
    cart_response = client.get(reverse("orders:cart_detail"))
    assert "Painel solar 550W" in cart_response.content.decode()
    assert "R$ 1799,80" in cart_response.content.decode()


@pytest.mark.django_db
def test_cart_never_adds_more_than_available_stock(client, product):
    client.post(
        reverse("orders:cart_add", kwargs={"product_id": product.id}),
        {"quantity": 99},
    )

    assert client.session["cart"] == {str(product.id): product.stock}


@pytest.mark.django_db
def test_cart_update_and_remove(client, product):
    client.post(
        reverse("orders:cart_add", kwargs={"product_id": product.id}),
        {"quantity": 2},
    )
    client.post(
        reverse("orders:cart_update", kwargs={"product_id": product.id}),
        {"quantity": 3},
    )
    assert client.session["cart"] == {str(product.id): 3}

    client.post(reverse("orders:cart_remove", kwargs={"product_id": product.id}))
    assert client.session["cart"] == {}


@pytest.mark.django_db
def test_inactive_product_cannot_be_added(client, product):
    product.is_active = False
    product.save(update_fields=["is_active"])

    response = client.post(
        reverse("orders:cart_add", kwargs={"product_id": product.id}),
        {"quantity": 1},
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_course_cannot_be_added_to_physical_cart(client, product):
    product.product_type = Product.ProductType.COURSE
    product.save(update_fields=["product_type"])

    response = client.post(
        reverse("orders:cart_add", kwargs={"product_id": product.id}),
        {"quantity": 1},
    )

    assert response.status_code == 404
