from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from products.catalog import SEPARATE_CATEGORY_SLUGS
from products.models import Category, Product


def product_list(request):
    products = Product.objects.filter(
        is_active=True,
        category__is_active=True,
    ).select_related("category")
    categories = Category.objects.filter(is_active=True)

    search_query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("categoria", "").strip()

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    if category_slug == "equipamentos":
        products = products.filter(
            product_type=Product.ProductType.PHYSICAL,
        ).exclude(category__slug__in=SEPARATE_CATEGORY_SLUGS)
    elif category_slug:
        products = products.filter(category__slug=category_slug)

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": categories,
        "search_query": search_query,
        "selected_category": category_slug,
    }
    return render(request, "products/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category"),
        slug=slug,
        is_active=True,
        category__is_active=True,
    )
    return render(request, "products/product_detail.html", {"product": product})
