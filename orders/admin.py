from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity", "subtotal")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "customer_name", "user", "status", "total", "created_at")
    list_filter = ("status", "payment_provider", "created_at")
    search_fields = ("number", "customer_name", "customer_email", "user__email", "provider_order_id")
    readonly_fields = ("number", "subtotal", "total", "checkout_url", "created_at", "updated_at")
    inlines = (OrderItemInline,)
