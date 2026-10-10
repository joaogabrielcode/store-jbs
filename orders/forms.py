from django import forms
from django.core.validators import MaxValueValidator

from accounts.models import CustomerAddress

from .models import Order


BRAZILIAN_STATES = (
    ("", "Selecione o estado"),
    ("AC", "Acre"),
    ("AL", "Alagoas"),
    ("AP", "Amapá"),
    ("AM", "Amazonas"),
    ("BA", "Bahia"),
    ("CE", "Ceará"),
    ("DF", "Distrito Federal"),
    ("ES", "Espírito Santo"),
    ("GO", "Goiás"),
    ("MA", "Maranhão"),
    ("MT", "Mato Grosso"),
    ("MS", "Mato Grosso do Sul"),
    ("MG", "Minas Gerais"),
    ("PA", "Pará"),
    ("PB", "Paraíba"),
    ("PR", "Paraná"),
    ("PE", "Pernambuco"),
    ("PI", "Piauí"),
    ("RJ", "Rio de Janeiro"),
    ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"),
    ("RO", "Rondônia"),
    ("RR", "Roraima"),
    ("SC", "Santa Catarina"),
    ("SP", "São Paulo"),
    ("SE", "Sergipe"),
    ("TO", "Tocantins"),
)


class PurchaseQuantityForm(forms.Form):
    quantity = forms.IntegerField(label="Quantidade", min_value=1)

    def __init__(self, *args, stock, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity"].max_value = stock
        self.fields["quantity"].validators.append(MaxValueValidator(stock))


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = (
            "customer_name",
            "customer_email",
            "customer_phone",
            "shipping_postal_code",
            "shipping_address",
            "shipping_number",
            "shipping_complement",
            "shipping_neighborhood",
            "shipping_city",
            "shipping_state",
        )
        widgets = {"shipping_state": forms.Select(choices=BRAZILIAN_STATES)}

    def clean_shipping_state(self):
        return self.cleaned_data["shipping_state"].strip().upper()

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["saved_address"] = forms.ModelChoiceField(
            label="Usar endereço salvo",
            queryset=CustomerAddress.objects.none(),
            required=False,
            empty_label="Preencher um novo endereço",
        )
        if user and user.is_authenticated:
            profile = getattr(user, "profile", None)
            self.fields["saved_address"].queryset = user.addresses.all()
            self.initial.setdefault("saved_address", user.addresses.filter(is_default=True).first())
            for field_name in (
                "shipping_postal_code",
                "shipping_address",
                "shipping_number",
                "shipping_neighborhood",
                "shipping_city",
                "shipping_state",
            ):
                self.fields[field_name].required = False
            self.initial.setdefault("customer_name", user.get_full_name())
            self.initial.setdefault("customer_email", user.email)
            self.initial.setdefault("customer_phone", profile.phone if profile else "")
        self.fields["shipping_postal_code"].widget.attrs.update(
            {"inputmode": "numeric", "autocomplete": "postal-code", "maxlength": 9}
        )
        self.fields["customer_name"].widget.attrs["autocomplete"] = "name"
        self.fields["customer_email"].widget.attrs["autocomplete"] = "email"
        self.fields["customer_phone"].widget.attrs["autocomplete"] = "tel"
        self.fields["shipping_address"].widget.attrs["autocomplete"] = "street-address"
        self.fields["shipping_number"].widget.attrs["autocomplete"] = "address-line2"
        self.fields["shipping_state"].widget.attrs["autocomplete"] = "address-level1"

    def clean(self):
        cleaned_data = super().clean()
        saved_address = cleaned_data.get("saved_address")
        if saved_address:
            address_fields = {
                "shipping_postal_code": "postal_code",
                "shipping_address": "address",
                "shipping_number": "number",
                "shipping_complement": "complement",
                "shipping_neighborhood": "neighborhood",
                "shipping_city": "city",
                "shipping_state": "state",
            }
            for field_name, address_field in address_fields.items():
                cleaned_data[field_name] = getattr(saved_address, address_field)
        else:
            for field_name in (
                "shipping_postal_code",
                "shipping_address",
                "shipping_number",
                "shipping_neighborhood",
                "shipping_city",
                "shipping_state",
            ):
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, "Informe este campo ou escolha um endereço salvo.")
        return cleaned_data
