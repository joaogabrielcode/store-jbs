from django.urls import path
from django.views.generic import RedirectView

from . import views


app_name = "products"

urlpatterns = [
    path(
        "",
        RedirectView.as_view(
            pattern_name="core:home", permanent=True, query_string=True,
        ),
        name="product_list",
    ),
    path("<slug:slug>/", views.product_detail, name="product_detail"),
]
