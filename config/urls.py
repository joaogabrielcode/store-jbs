from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from orders.views import order_confirmation
from hotmart.views import hotmart_webhook


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("produtos/", include("products.urls")),
    path("cursos/", include("hotmart.urls")),
    path("webhooks/hotmart/", hotmart_webhook, name="hotmart_webhook"),
    path("conta/", include("accounts.urls")),
    path("carrinho/", include("orders.urls")),
    path("webhooks/", include("payments.urls")),
    path("pedidos/<uuid:number>/<str:result>/", order_confirmation, name="order_confirmation"),
    path("api/", include("config.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
