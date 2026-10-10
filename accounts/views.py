from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from orders.models import Order

from .forms import AccountAuthenticationForm, CustomerAddressForm, ProfileForm, SignUpForm
from .models import CustomerProfile

User = get_user_model()


def _send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verification_url = request.build_absolute_uri(
        reverse("accounts:verify_email", kwargs={"uidb64": uid, "token": token})
    )
    send_mail(
        "Confirme seu e-mail: JBS Solar",
        render_to_string(
            "accounts/emails/verify_email.txt",
            {"user": user, "verification_url": verification_url},
        ),
        None,
        [user.email],
        fail_silently=False,
    )


def signup(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        _send_verification_email(request, user)
        return redirect("accounts:verification_sent")
    return render(request, "accounts/signup.html", {"form": form})


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = AccountAuthenticationForm
    redirect_authenticated_user = True


@login_required
def account_logout(request):
    if request.method != "POST":
        return redirect("accounts:dashboard")
    logout(request)
    messages.success(request, "Você saiu da sua conta.")
    return redirect("core:home")


def verification_sent(request):
    return render(request, "accounts/verification_sent.html")


def verify_email(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        raise Http404("Link de verificação inválido.")
    if not default_token_generator.check_token(user, token):
        return render(request, "accounts/verification_invalid.html", status=400)
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    profile.email_verified = True
    profile.save(update_fields=["email_verified"])
    messages.success(request, "E-mail confirmado. Agora você já pode entrar.")
    return redirect("accounts:login")


@login_required
def dashboard(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "accounts/dashboard.html", {"orders": orders})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        email_changed = form.cleaned_data["email"] != request.user.email
        user = form.save()
        if email_changed:
            profile, _ = CustomerProfile.objects.get_or_create(user=user)
            profile.email_verified = False
            profile.save(update_fields=["email_verified"])
        if email_changed:
            _send_verification_email(request, user)
            messages.success(request, "Dados atualizados. Enviamos um novo link para confirmar o e-mail.")
        else:
            messages.success(request, "Dados atualizados com sucesso.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    return render(request, "accounts/addresses.html", {"addresses": addresses})


@login_required
def address_create(request):
    form = CustomerAddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        if not request.user.addresses.exists():
            address.is_default = True
        with transaction.atomic():
            if address.is_default:
                request.user.addresses.filter(is_default=True).update(is_default=False)
            address.save()
        messages.success(request, "Endereço adicionado.")
        return redirect("accounts:addresses")
    return render(request, "accounts/address_form.html", {"form": form, "title": "Novo endereço"})


@login_required
def address_update(request, address_id):
    address = get_object_or_404(request.user.addresses, pk=address_id)
    form = CustomerAddressForm(request.POST or None, instance=address)
    if request.method == "POST" and form.is_valid():
        address = form.save(commit=False)
        with transaction.atomic():
            if address.is_default:
                request.user.addresses.filter(is_default=True).exclude(pk=address.pk).update(is_default=False)
            address.save()
        messages.success(request, "Endereço atualizado.")
        return redirect("accounts:addresses")
    return render(request, "accounts/address_form.html", {"form": form, "title": "Editar endereço"})


@login_required
def address_delete(request, address_id):
    if request.method != "POST":
        return redirect("accounts:addresses")
    address = get_object_or_404(request.user.addresses, pk=address_id)
    was_default = address.is_default
    with transaction.atomic():
        address.delete()
        if was_default:
            replacement = request.user.addresses.first()
            if replacement:
                replacement.is_default = True
                replacement.save(update_fields=["is_default", "updated_at"])
    messages.success(request, "Endereço removido.")
    return redirect("accounts:addresses")
