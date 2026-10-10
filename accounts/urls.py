from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import reverse_lazy

from .views import (
    AccountLoginView,
    account_logout,
    address_create,
    address_delete,
    address_list,
    address_update,
    dashboard,
    profile,
    signup,
    verification_sent,
    verify_email,
)

app_name = "accounts"

urlpatterns = [
    path("cadastro/", signup, name="signup"),
    path("entrar/", AccountLoginView.as_view(), name="login"),
    path("sair/", account_logout, name="logout"),
    path("verificar-email/", verification_sent, name="verification_sent"),
    path("verificar-email/<uidb64>/<token>/", verify_email, name="verify_email"),
    path("minha-conta/", dashboard, name="dashboard"),
    path("minha-conta/perfil/", profile, name="profile"),
    path("minha-conta/enderecos/", address_list, name="addresses"),
    path("minha-conta/enderecos/novo/", address_create, name="address_create"),
    path("minha-conta/enderecos/<int:address_id>/editar/", address_update, name="address_update"),
    path("minha-conta/enderecos/<int:address_id>/remover/", address_delete, name="address_delete"),
    path(
        "senha/redefinir/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/emails/password_reset.txt",
            subject_template_name="accounts/emails/password_reset_subject.txt",
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),
    path("senha/redefinir/enviado/", auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path(
        "senha/redefinir/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path("senha/redefinir/concluido/", auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"), name="password_reset_complete"),
]
