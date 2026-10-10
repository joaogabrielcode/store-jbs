from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import CustomerAddress, CustomerProfile

User = get_user_model()


class SignUpForm(forms.Form):
    first_name = forms.CharField(label="Nome", max_length=150)
    last_name = forms.CharField(label="Sobrenome", max_length=150)
    email = forms.EmailField(label="E-mail", max_length=150)
    phone = forms.CharField(label="Telefone", max_length=30, required=False)
    password1 = forms.CharField(label="Senha", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirme a senha", widget=forms.PasswordInput)
    accept_terms = forms.BooleanField(
        label="Aceito os termos de uso e a política de privacidade."
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "As senhas não coincidem.")
        if password1:
            try:
                validate_password(password1)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data["email"].lower(),
            email=self.cleaned_data["email"].lower(),
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
        )
        CustomerProfile.objects.create(
            user=user,
            phone=self.cleaned_data["phone"],
            terms_accepted_at=timezone.now(),
        )
        return user


class AccountAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="E-mail", widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        profile = CustomerProfile.objects.filter(user=user).first()
        if profile and not profile.email_verified and not user.is_staff:
            raise forms.ValidationError(
                "Confirme seu e-mail antes de entrar. Verifique sua caixa de entrada.",
                code="email_unverified",
            )


class ProfileForm(forms.Form):
    first_name = forms.CharField(label="Nome", max_length=150)
    last_name = forms.CharField(label="Sobrenome", max_length=150)
    email = forms.EmailField(label="E-mail")
    phone = forms.CharField(label="Telefone", max_length=30, required=False)

    def __init__(self, *args, user, **kwargs):
        self.user = user
        self.profile, _ = CustomerProfile.objects.get_or_create(user=user)
        initial = kwargs.setdefault("initial", {})
        initial.update({
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": self.profile.phone,
        })
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(~Q(pk=self.user.pk)).filter(
            Q(email__iexact=email) | Q(username__iexact=email)
        ).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def save(self):
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.email = self.cleaned_data["email"].lower()
        self.user.username = self.user.email
        self.user.save(update_fields=["first_name", "last_name", "email", "username"])
        self.profile.phone = self.cleaned_data["phone"]
        self.profile.save(update_fields=["phone"])
        return self.user


class CustomerAddressForm(forms.ModelForm):
    class Meta:
        model = CustomerAddress
        exclude = ("user", "created_at", "updated_at")
        labels = {
            "label": "Identificação",
            "postal_code": "CEP",
            "address": "Endereço",
            "number": "Número",
            "complement": "Complemento",
            "neighborhood": "Bairro",
            "city": "Cidade",
            "state": "Estado",
            "is_default": "Usar como endereço principal",
        }
        widgets = {"state": forms.TextInput(attrs={"maxlength": 2})}

    def clean_state(self):
        return self.cleaned_data["state"].strip().upper()
