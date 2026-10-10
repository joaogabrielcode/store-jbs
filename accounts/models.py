from django.conf import settings
from django.db import models
from django.db.models import Q


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="usuário",
    )
    phone = models.CharField("telefone", max_length=30, blank=True)
    email_verified = models.BooleanField("e-mail verificado", default=False)
    terms_accepted_at = models.DateTimeField("termos aceitos em", null=True, blank=True)

    class Meta:
        verbose_name = "perfil do cliente"
        verbose_name_plural = "perfis dos clientes"

    def __str__(self):
        return self.user.email


class CustomerAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name="usuário",
    )
    label = models.CharField("identificação", max_length=60, default="Principal")
    postal_code = models.CharField("CEP", max_length=9)
    address = models.CharField("endereço", max_length=200)
    number = models.CharField("número", max_length=20)
    complement = models.CharField("complemento", max_length=120, blank=True)
    neighborhood = models.CharField("bairro", max_length=120)
    city = models.CharField("cidade", max_length=120)
    state = models.CharField("estado", max_length=2)
    is_default = models.BooleanField("principal", default=False)
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        ordering = ["-is_default", "label", "id"]
        verbose_name = "endereço do cliente"
        verbose_name_plural = "endereços dos clientes"
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_default=True),
                name="one_default_address_per_user",
            )
        ]

    def __str__(self):
        return f"{self.label} — {self.address}, {self.number}"
