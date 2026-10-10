from django.urls import reverse
import pytest


@pytest.mark.django_db
def test_home_page_renders(client):
    response = client.get(reverse("core:home"), headers={"Host": "localhost"})

    assert response.status_code == 200
    assert "JBS Solar" in response.content.decode()
    assert "products/product_list.html" in [template.name for template in response.templates]
