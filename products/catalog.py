STORE_CATEGORIES = (
    {"name": "Kits solares", "slug": "kits-solares"},
    {"name": "Softwares", "slug": "softwares", "highlighted": True},
    {"name": "Cursos", "slug": "cursos"},
    {"name": "Equipamentos", "slug": "equipamentos"},
    {"name": "Documentos", "slug": "documentos"},
)

SEPARATE_CATEGORY_SLUGS = tuple(
    category["slug"]
    for category in STORE_CATEGORIES
    if category["slug"] != "equipamentos"
)
