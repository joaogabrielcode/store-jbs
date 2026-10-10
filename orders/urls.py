from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("adicionar/<int:product_id>/", views.cart_add, name="cart_add"),
    path("atualizar/<int:product_id>/", views.cart_update, name="cart_update"),
    path("remover/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("comprar/<int:product_id>/", views.buy_now, name="buy_now"),
    path(
        "checkout/produto/<int:product_id>/<int:quantity>/",
        views.checkout,
        name="direct_checkout",
    ),
    path("<uuid:number>/<str:result>/", views.order_confirmation, name="order_confirmation"),
]
