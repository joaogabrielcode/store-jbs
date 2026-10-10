from django.urls import path

from .views import mercadopago_webhook

app_name = "payments"

urlpatterns = [
    path("mercadopago/", mercadopago_webhook, name="mercadopago_webhook"),
]
