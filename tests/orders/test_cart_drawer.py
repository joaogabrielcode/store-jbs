from decimal import Decimal

import pytest
from django.urls import reverse

from products.models import Category, Product


@pytest.mark.django_db
def test_ajax_cart_add_returns_drawer_content(client):
    category = Category.objects.create(name="Painéis", slug="paineis")
    product = Product.objects.create(
        category=category,
        name="Painel solar 550W",
        slug="painel-solar-550w-drawer",
        price=Decimal("899.90"),
        stock=4,
    )

    response = client.post(
        reverse("orders:cart_add", kwargs={"product_id": product.id}),
        {"quantity": 2},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["cart_count"] == 2
    assert "Painel solar 550W" in payload["html"]
    assert "R$ 1799,80" in payload["html"]
    assert 'href="/carrinho/checkout/"' in payload["html"]
