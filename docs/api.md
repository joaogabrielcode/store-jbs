# API

O site principal é renderizado com Django Templates. O Django REST Framework fica reservado para integrações, endpoints assíncronos e clientes externos.

## Versionamento

A base versionada está disponível em:

```text
/api/v1/
```

Ainda não há endpoints de negócio. Quando forem solicitados, produtos, categorias e pedidos deverão ser adicionados dentro dessa versão, com serializers, permissions e testes próprios.

## Regras

- Não criar APIs sem necessidade do produto.
- Validar entrada no serializer e no backend.
- Não confiar em preço, total ou status de pagamento enviados pelo cliente.
- Usar autenticação e permissions em endpoints privados.
- Manter regras de negócio compartilhadas entre Templates e API no backend.
