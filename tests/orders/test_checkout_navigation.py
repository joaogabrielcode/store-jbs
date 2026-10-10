from decimal import Decimal

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

from products.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
def test_cart_checkout_link_opens_checkout_page(client):
    category = Category.objects.create(name="Kits", slug="kits-checkout")
    product = Product.objects.create(
        category=category,
        name="Kit solar",
        slug="kit-solar-checkout",
        price=Decimal("100.00"),
        stock=2,
    )
    client.post(reverse("orders:cart_add", kwargs={"product_id": product.id}))

    response = client.get(reverse("orders:checkout"))

    assert response.status_code == 200
    assert "Finalizar" in response.content.decode()


@pytest.mark.django_db
def test_authenticated_checkout_without_profile_phone_renders_safely(client):
    category = Category.objects.create(name="Materiais", slug="materiais-checkout")
    product = Product.objects.create(
        category=category,
        name="Cabo solar",
        slug="cabo-solar-checkout",
        price=Decimal("50.00"),
        stock=2,
    )
    user = User.objects.create_user(
        username="sem-perfil@example.com",
        email="sem-perfil@example.com",
        password="UmaSenhaForte123!",
        first_name="Cliente",
    )
    client.force_login(user)
    client.post(reverse("orders:cart_add", kwargs={"product_id": product.id}))

    response = client.get(reverse("orders:checkout"))

    assert response.status_code == 200
    assert response.context["form"].initial["customer_phone"] == ""
