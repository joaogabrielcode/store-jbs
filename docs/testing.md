# Testes

O projeto usa `pytest` e `pytest-django`. A configuração está em `pytest.ini` e os testes ficam em `tests/`, organizados por área.

## Executar

Com as variáveis do `.env` carregadas e o PostgreSQL disponível:

```bash
pytest
```

Também é possível executar verificações do Django:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

A estrutura está preparada para testes de models, services, serializers, endpoints e permissions. Pedidos, compra direta, pagamentos e Hotmart já possuem testes de regras críticas e mocks das APIs externas.

## Organização esperada

- `tests/core/`: páginas e funcionalidades compartilhadas;
- `tests/products/`: models, catálogo e serializers de produtos;
- `tests/orders/`: regras de pedidos e transações;
- `tests/accounts/`: usuários, clientes e permissions;
- `tests/payments/`: integrações e confirmação de pagamentos quando forem implementadas;
- `tests/api/`: contratos e endpoints versionados.

Priorize testes de regras críticas e use TDD quando a feature tiver uma regra de
negócio nova ou uma API com contrato relevante. Não é necessário criar testes ou
dependências de domínio antes da implementação correspondente.

## Integrações

`tests/payments/` cobre payload e idempotency key da Orders API, assinatura
oficial, referência/total, estados, refunds e falhas. `tests/hotmart/` cobre
sincronização paginada, ofertas, preservação local, erros, páginas, Admin e
webhooks idempotentes. Não executar esses testes contra a API real.

`tests/orders/test_checkout_idempotency.py` inclui threads com conexões
PostgreSQL separadas para validar bloqueio da tentativa e reenvio durante a
chamada ao provedor. Também cobre sessão, URL, carrinho alterado, token expirado
e resposta inconclusiva. `tests/payments/test_expiration.py` cobre vencimento,
cancelamento confirmado, pagamento concorrente, erro de rede e estoque seguro.
