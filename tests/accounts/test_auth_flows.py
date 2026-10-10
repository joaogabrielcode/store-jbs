from datetime import timedelta
from unittest.mock import patch
from urllib.parse import urlsplit

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import CustomerProfile

User = get_user_model()
pytestmark = pytest.mark.django_db
OLD_PASSWORD = "UmaSenhaForte123!"
NEW_PASSWORD = "OutraSenhaSegura456!"


@pytest.fixture
def verified_user():
    user = User.objects.create_user(
        username="cliente@example.com", email="cliente@example.com", password=OLD_PASSWORD,
    )
    CustomerProfile.objects.create(user=user, email_verified=True)
    return user


@pytest.fixture(autouse=True)
def local_email(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


def email_path(message):
    return urlsplit(next(line for line in message.body.splitlines() if line.startswith("http"))).path


def reset_path(user, token=None):
    return reverse("accounts:password_reset_confirm", kwargs={
        "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": token or default_token_generator.make_token(user),
    })


def test_signup_confirmation_and_login(client, mailoutbox):
    response = client.post(reverse("accounts:signup"), {
        "first_name": "João", "last_name": "Cliente", "email": "CLIENTE@example.com",
        "phone": "", "password1": OLD_PASSWORD, "password2": OLD_PASSWORD,
        "accept_terms": "on",
    })
    assert response.url == reverse("accounts:verification_sent")
    user = User.objects.get(email="cliente@example.com")
    assert not user.profile.email_verified
    assert "_auth_user_id" not in client.session
    confirmation = client.get(email_path(mailoutbox[0]))
    assert confirmation.url == reverse("accounts:login")
    user.profile.refresh_from_db()
    assert user.profile.email_verified
    login = client.post(reverse("accounts:login"), {"username": "CLIENTE@example.com", "password": OLD_PASSWORD})
    assert login.url == reverse("accounts:dashboard")
    assert client.get(login.url).status_code == 200
    assert client.get(reverse("accounts:login")).url == reverse("accounts:dashboard")


def test_anonymous_account_redirect_uses_store_login(client):
    path = reverse("accounts:dashboard")
    assert client.get(path).url == reverse("accounts:login") + "?next=" + path


@pytest.mark.parametrize("destination", ["/conta/minha-conta/perfil/", "https://example.net/"])
def test_login_next_accepts_only_local_destination(client, verified_user, destination):
    response = client.post(reverse("accounts:login"), {
        "username": verified_user.email, "password": OLD_PASSWORD, "next": destination,
    })
    expected = destination if destination.startswith("/") else reverse("accounts:dashboard")
    assert response.url == expected


def test_password_reset_full_flow_and_used_token(client, verified_user, mailoutbox):
    response = client.post(reverse("accounts:password_reset"), {"email": verified_user.email})
    assert response.url == reverse("accounts:password_reset_done")
    assert client.get(response.url).status_code == 200
    assert len(mailoutbox) == 1
    token_path = email_path(mailoutbox[0])
    confirmation = client.get(token_path, follow=True)
    assert confirmation.context["validlink"]
    form_path = confirmation.request["PATH_INFO"]
    changed = client.post(form_path, {"new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD})
    assert changed.url == reverse("accounts:password_reset_complete")
    assert client.get(changed.url).status_code == 200
    verified_user.refresh_from_db()
    assert verified_user.check_password(NEW_PASSWORD)
    assert not verified_user.check_password(OLD_PASSWORD)
    assert "_auth_user_id" not in client.session
    reused = client.get(token_path, follow=True)
    assert not reused.context["validlink"]
    login = client.post(reverse("accounts:login"), {"username": verified_user.email, "password": NEW_PASSWORD})
    assert login.url == reverse("accounts:dashboard")


def test_unknown_email_gets_same_reset_confirmation(client, verified_user, mailoutbox):
    known = client.post(reverse("accounts:password_reset"), {"email": verified_user.email})
    unknown = client.post(reverse("accounts:password_reset"), {"email": "inexistente@example.com"})
    assert unknown.url == known.url == reverse("accounts:password_reset_done")
    assert len(mailoutbox) == 1


@pytest.mark.parametrize("invalid_token", ["tampered", "expired"])
def test_invalid_reset_token_cannot_change_password(client, verified_user, settings, invalid_token):
    if invalid_token == "expired":
        settings.PASSWORD_RESET_TIMEOUT = 60
        with patch.object(default_token_generator, "_now", return_value=default_token_generator._now() - timedelta(minutes=2)):
            token = default_token_generator.make_token(verified_user)
    else:
        token = "invalid-token"
    response = client.get(reset_path(verified_user, token), follow=True)
    assert not response.context["validlink"]
    assert "Solicitar outro link" in response.content.decode()
    verified_user.refresh_from_db()
    assert verified_user.check_password(OLD_PASSWORD)


def test_reset_rejects_weak_or_mismatched_password(client, verified_user):
    confirmation = client.get(reset_path(verified_user), follow=True)
    path = confirmation.request["PATH_INFO"]
    for password1, password2 in [("123", "123"), (NEW_PASSWORD, "Diferente789!")]:
        response = client.post(path, {"new_password1": password1, "new_password2": password2})
        assert response.status_code == 200
        assert response.context["form"].errors
        verified_user.refresh_from_db()
        assert verified_user.check_password(OLD_PASSWORD)


@pytest.mark.parametrize("route", ["accounts:signup", "accounts:login", "accounts:password_reset"])
def test_auth_posts_require_csrf(route):
    assert Client(enforce_csrf_checks=True).post(reverse(route), {}).status_code == 403


def test_duplicate_signup_does_not_send_email(client, verified_user, mailoutbox):
    response = client.post(reverse("accounts:signup"), {
        "first_name": "João", "last_name": "Cliente", "email": "CLIENTE@example.com",
        "password1": OLD_PASSWORD, "password2": OLD_PASSWORD, "accept_terms": "on",
    })
    assert "Já existe uma conta" in response.content.decode()
    assert User.objects.count() == 1
    assert not mailoutbox


def test_reset_does_not_confirm_unverified_account(client, verified_user, mailoutbox):
    CustomerProfile.objects.filter(user=verified_user).update(email_verified=False)
    client.post(reverse("accounts:password_reset"), {"email": verified_user.email})
    confirmation = client.get(email_path(mailoutbox[0]), follow=True)
    client.post(confirmation.request["PATH_INFO"], {"new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD})
    response = client.post(reverse("accounts:login"), {"username": verified_user.email, "password": NEW_PASSWORD})
    assert "Confirme seu e-mail" in response.content.decode()
    assert "_auth_user_id" not in client.session


def test_reset_confirmation_post_requires_csrf(verified_user):
    client = Client(enforce_csrf_checks=True)
    confirmation = client.get(reset_path(verified_user), follow=True)
    response = client.post(confirmation.request["PATH_INFO"], {
        "new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD,
    })
    assert response.status_code == 403
    verified_user.refresh_from_db()
    assert verified_user.check_password(OLD_PASSWORD)


def test_tampered_verification_does_not_confirm_email(client, verified_user):
    CustomerProfile.objects.filter(user=verified_user).update(email_verified=False)
    path = reverse("accounts:verify_email", kwargs={
        "uidb64": urlsafe_base64_encode(force_bytes(verified_user.pk)),
        "token": "invalid-token",
    })
    assert client.get(path).status_code == 400
    verified_user.profile.refresh_from_db()
    assert not verified_user.profile.email_verified


@pytest.mark.parametrize("changes", [
    {"accept_terms": ""},
    {"password1": "123", "password2": "123"},
    {"email": "a" * 140 + "@example.com"},
])
def test_invalid_signup_does_not_create_account(client, mailoutbox, changes):
    data = {
        "first_name": "João", "last_name": "Cliente", "email": "cliente@example.com",
        "password1": OLD_PASSWORD, "password2": OLD_PASSWORD, "accept_terms": "on",
    }
    data.update(changes)
    response = client.post(reverse("accounts:signup"), data)
    assert response.status_code == 200
    assert response.context["form"].errors
    assert not User.objects.exists()
    assert not mailoutbox
