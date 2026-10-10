from orders.models import Order
from products.catalog import STORE_CATEGORIES
from products.models import Product


def store_navigation(request):
    return {
        "store_menu_categories": STORE_CATEGORIES,
    }


def admin_dashboard(request):
    if request.path.rstrip("/") != "/admin" or not request.user.is_staff:
        return {}

    return {
        "admin_stats": {
            "active_products": Product.objects.filter(is_active=True).count(),
            "low_stock": Product.objects.filter(is_active=True, stock__lte=5).count(),
            "pending_orders": Order.objects.filter(status=Order.Status.PENDING_PAYMENT).count(),
            "paid_orders": Order.objects.filter(
                status__in=[Order.Status.PAID, Order.Status.PROCESSING]
            ).count(),
        }
    }
