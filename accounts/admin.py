from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import CustomerAddress, CustomerProfile

User = get_user_model()
admin.site.unregister(User)


@admin.register(User)
class AccountUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "groups")
    search_fields = ("username", "email", "first_name", "last_name")


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ("label", "user", "city", "state", "is_default")
    list_filter = ("state", "is_default")
    search_fields = ("user__email", "user__first_name", "postal_code", "city")
    list_select_related = ("user",)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "email_verified", "terms_accepted_at")
    list_filter = ("email_verified",)
    search_fields = ("user__username", "user__email", "phone")
    list_select_related = ("user",)
