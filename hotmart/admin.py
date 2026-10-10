from django.contrib import admin
from django.db import models
from .models import Course, WebhookEvent


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "price", "currency", "is_visible", "is_featured", "sort_order", "last_synced_at")
    list_filter = ("status", "is_visible", "is_featured")
    formfield_overrides = {models.URLField: {"assume_scheme": "https"}}
    search_fields = ("name", "hotmart_id", "slug")
    readonly_fields = ("hotmart_id", "hotmart_ucode", "name", "status", "offer_code", "checkout_url", "price", "currency", "last_synced_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event", "hotmart_id", "transaction", "purchase_status", "received_at")
    list_filter = ("event", "purchase_status")
    search_fields = ("event_id", "transaction")
    readonly_fields = tuple(field.name for field in WebhookEvent._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
