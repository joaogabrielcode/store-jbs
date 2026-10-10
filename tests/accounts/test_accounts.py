import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import CustomerAddress, CustomerProfile

User = get_user_model()


@pytest.mark.django_db
def test_signup_creates_user_profile_and_requires_email_verification(client, mailoutbox, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    response = client.post(
        reverse("accounts:signup"),
        {
            "first_name": "João",
            "last_name": "Cliente",
            "email": "cliente@example.com",
            "phone": "11999999999",
            "password1": "UmaSenhaForte123!",
            "password2": "UmaSenhaForte123!",
            "accept_terms": "on",
        },
    )

    assert response.status_code == 302
    user = User.objects.get(email="cliente@example.com")
    assert user.username == user.email
    assert user.profile.phone == "11999999999"
    assert not user.profile.email_verified
    assert len(mailoutbox) == 1

    login_response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "UmaSenhaForte123!"},
    )
    assert "Confirme seu e-mail" in login_response.content.decode()


@pytest.mark.django_db
def test_verified_user_can_access_account_and_save_address(client):
    user = User.objects.create_user(
        username="cliente@example.com",
        email="cliente@example.com",
        password="UmaSenhaForte123!",
        first_name="João",
    )
    CustomerProfile.objects.create(user=user, email_verified=True)
    client.force_login(user)

    response = client.post(
        reverse("accounts:address_create"),
        {
            "label": "Casa",
            "postal_code": "01001-000",
            "address": "Praça da Sé",
            "number": "1",
            "complement": "Apto 2",
            "neighborhood": "Sé",
            "city": "São Paulo",
            "state": "SP",
            "is_default": "on",
        },
    )

    assert response.status_code == 302
    assert CustomerAddress.objects.filter(user=user, is_default=True).exists()
    assert client.get(reverse("accounts:dashboard")).status_code == 200
