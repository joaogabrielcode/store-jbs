from decimal import Decimal

import pytest
from django.urls import reverse

from products.models import Category, Product


@pytest.fixture
def catalog_data(db):
    category = Category.objects.create(name="Painéis", slug="paineis")
    other_category = Category.objects.create(name="Inversores", slug="inversores")
    active_product = Product.objects.create(
        category=category,
        name="Painel solar 550W",
        slug="painel-solar-550w",
        description="Painel para geração residencial.",
        price=Decimal("899.90"),
        stock=10,
    )
    Product.objects.create(
        category=category,
        name="Produto inativo",
        slug="produto-inativo",
        price=Decimal("100.00"),
        is_active=False,
    )
    Product.objects.create(
        category=other_category,
        name="Inversor solar",
        slug="inversor-solar",
        price=Decimal("1999.90"),
        stock=2,
    )
    return active_product


@pytest.mark.django_db
def test_product_list_shows_only_active_products(client, catalog_data):
    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    assert catalog_data.name in response.content.decode()
    assert "Produto inativo" not in response.content.decode()


@pytest.mark.django_db
def test_product_list_filters_by_search_and_category(client, catalog_data):
    response = client.get(
        reverse("core:home"),
        {"q": "550W", "categoria": "paineis"},
    )

    assert response.status_code == 200
    assert "Painel solar 550W" in response.content.decode()
    assert "Inversor solar" not in response.content.decode()


@pytest.mark.parametrize(
    "query_string",
    ["", "q=painel+solar&categoria=paineis&page=2", "q=gera%C3%A7%C3%A3o"],
)
def test_previous_catalog_url_redirects_preserving_query_string(client, query_string):
    suffix = f"?{query_string}" if query_string else ""

    response = client.get(reverse("products:product_list") + suffix)

    assert response.status_code == 301
    assert response.url == reverse("core:home") + suffix


@pytest.mark.django_db
def test_home_catalog_pagination_preserves_filters(client, catalog_data):
    Product.objects.bulk_create([
        Product(
            category=catalog_data.category,
            name=f"Painel 550W {number}",
            slug=f"painel-550w-{number}",
            price=Decimal("899.90"),
            stock=1,
        )
        for number in range(12)
    ])

    response = client.get(
        reverse("core:home"),
        {"q": "550W", "categoria": "paineis", "page": 2},
    )

    assert response.status_code == 200
    assert response.context["page_obj"].number == 2
    assert response.context["page_obj"].paginator.count == 13
    assert len(response.context["products"]) == 1
    assert '?q=550W&categoria=paineis&page=1' in response.content.decode()


@pytest.mark.django_db
def test_product_detail_uses_slug(client, catalog_data):
    response = client.get(
        reverse("products:product_detail", kwargs={"slug": catalog_data.slug})
    )

    assert response.status_code == 200
    assert catalog_data.description in response.content.decode()


@pytest.mark.django_db
def test_product_detail_returns_404_for_inactive_product(client, catalog_data):
    response = client.get(
        reverse("products:product_detail", kwargs={"slug": "produto-inativo"})
    )

    assert response.status_code == 404


@pytest.fixture
def menu_catalog(db):
    products = {}
    for slug in [
        "kits-solares", "softwares", "cursos", "documentos", "equipamentos",
        "paineis", "inversores", "carregadores", "cabos", "formacao",
    ]:
        category = Category.objects.create(name=slug, slug=slug)
        products[slug] = Product.objects.create(
            category=category,
            name=f"Produto {slug}",
            slug=f"produto-{slug}",
            price=Decimal("100.00"),
            stock=1,
            product_type=(
                Product.ProductType.COURSE if slug in {"cursos", "formacao"}
                else Product.ProductType.PHYSICAL
            ),
        )
    return products


@pytest.mark.django_db
@pytest.mark.parametrize("slug", ["kits-solares", "softwares", "cursos", "documentos"])
def test_menu_category_filters_catalog(client, menu_catalog, slug):
    response = client.get(reverse("core:home"), {"categoria": slug})

    assert response.status_code == 200
    assert list(response.context["products"]) == [menu_catalog[slug]]


@pytest.mark.django_db
def test_equipment_groups_physical_products_without_other_menu_categories(client, menu_catalog):
    menu_catalog["cabos"].is_active = False
    menu_catalog["cabos"].save()
    category = menu_catalog["carregadores"].category
    category.is_active = False
    category.save()

    response = client.get(reverse("core:home"), {"categoria": "equipamentos"})

    assert response.status_code == 200
    assert set(response.context["products"]) == {
        menu_catalog["equipamentos"], menu_catalog["paineis"], menu_catalog["inversores"],
    }


@pytest.mark.django_db
def test_equipment_search_keeps_group_filter(client, menu_catalog):
    response = client.get(
        reverse("core:home"), {"categoria": "equipamentos", "q": "inversores"},
    )

    assert response.status_code == 200
    assert list(response.context["products"]) == [menu_catalog["inversores"]]


@pytest.mark.django_db
@pytest.mark.parametrize("slug", ["kits-solares", "softwares", "cursos", "equipamentos", "documentos"])
def test_empty_menu_category_keeps_navigation_and_shows_empty_state(client, slug):
    response = client.get(reverse("core:home"), {"categoria": slug})

    assert response.status_code == 200
    assert response.context["page_obj"].paginator.count == 0
    assert "Nenhum produto encontrado" in response.content.decode()
    expected_url = "/cursos/" if slug == "cursos" else f"/?categoria={slug}"
    assert f'href="{expected_url}"' in response.content.decode()
