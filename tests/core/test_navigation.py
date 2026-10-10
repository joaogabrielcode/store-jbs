import pytest
from django.urls import reverse

from products.models import Category


@pytest.mark.django_db
def test_catalog_sidebar_shows_only_active_categories(client):
    Category.objects.create(name="Painéis", slug="paineis")
    Category.objects.create(name="Oculta", slug="oculta", is_active=False)

    response = client.get(reverse("core:home"))

    content = response.content.decode()
    assert "Painéis" in content
    assert "?categoria=paineis" in content
    assert "Oculta" not in content
    assert 'action="/"' in content
    assert 'href="?categoria=paineis"' in content
    assert 'id="categorias"' in content
    assert 'id="produtos"' in content
    assert '#destaques' not in content


@pytest.mark.django_db
@pytest.mark.parametrize("selected", ["", "kits-solares", "softwares", "cursos", "equipamentos", "documentos"])
def test_menu_order_highlight_and_current_item(client, selected):
    response = client.get(reverse("core:home"), {"categoria": selected})
    content = response.content.decode()
    menu = content.split('<nav id="main-menu"', 1)[1].split("</nav>", 1)[0]
    names = ["Início", "Kits solares", "Softwares", "Cursos", "Equipamentos", "Documentos"]

    positions = [menu.index(f">{name}</a>") for name in names]
    assert positions == sorted(positions)
    assert "nav-highlight" in menu
    assert menu.count('aria-current="page"') == 1
    current_url = "/cursos/" if selected == "cursos" else (f"/?categoria={selected}" if selected else "/")
    assert f'href="{current_url}" aria-current="page"' in menu
    for slug in ["kits-solares", "softwares", "cursos", "equipamentos", "documentos"]:
        expected_url = "/cursos/" if slug == "cursos" else f"/?categoria={slug}"
        assert f'href="{expected_url}"' in menu
    assert "Ofertas" not in menu
    assert "Loja JBS" not in menu
    assert "Materiais" not in menu
