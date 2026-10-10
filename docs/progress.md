# Estado atual do projeto

Este arquivo é o ponto de retomada do desenvolvimento da JBS Solar Store.
Atualize-o ao concluir uma etapa importante ou ao interromper uma tarefa.

## Status

- **Fase atual:** 5 — Contas de clientes e área do cliente
- **Situação:** loja física funcional; contas, endereços, pedidos vinculados e carrinho flutuante implementados; Mercado Pago preparado
- **Última etapa concluída:** cadastro, login, verificação de e-mail, recuperação de senha, perfil, endereços e histórico de pedidos
- **Próxima tarefa:** configurar e testar o envio real de e-mails e validar o fluxo completo de pagamento no Mercado Pago

## Ponto exato de retomada — 30/09/2026

Foi identificado que a barra lateral do `/admin` estava quebrada porque
`static/admin/css/jbs-admin.css` sobrescrevia a largura estrutural nativa do
Django em `#nav-sidebar`. A regra `width: 235px` foi removida para preservar o
layout nativo (`flex`, estados oculto/aberto e responsividade), mantendo apenas
cores, bordas e tipografia personalizadas. O cache do CSS foi atualizado para
`v=admin-02` em `templates/admin/base_site.html`.

As contas usam o usuário nativo do Django e o app `accounts` mantém um
`CustomerProfile` separado, evitando trocar `AUTH_USER_MODEL` depois de o
Admin já ter migrations aplicadas. O cadastro exige aceite dos termos, envia
verificação de e-mail, bloqueia login não verificado e oferece recuperação de
senha. Usuários autenticados podem editar dados, salvar endereços e consultar
pedidos vinculados; o checkout continua aceitando visitantes.

Também foi observado que os testes executados diretamente no host não conseguem
resolver o host Docker `db` quando o Compose não está acessível. A última
execução confiável anterior foi de 18 testes passando dentro da rede do Docker.
Após restabelecer o acesso ao Docker, repetir `pytest -q` no ambiente do
Compose.

Nesta retomada, o CSS da loja foi escopado sob `.store-app`, o admin passou a
usar `body.admin-interface`, e o stylesheet exclusivo do painel foi movido para
`static/admin/css/jbs-admin.css`. O storefront não carrega assets do admin e o
admin não carrega `main.css`.

## Fundação concluída

- Monólito Django modular configurado.
- Apps `core`, `products`, `orders`, `accounts` e `payments` criados.
- Django Templates configurado como frontend principal.
- DRF reservado para `/api/v1/`.
- PostgreSQL e Docker Compose configurados.
- `.env.example`, `.gitignore`, `README.md` e documentação inicial criados.
- Skills do projeto instaladas em `.agents/skills/`.
- Teste inicial da página principal criado.
- Models `Category` e `Product` criados em `products/models.py`.
- Migration inicial criada em `products/migrations/0001_initial.py`.
- Models registrados e configurados no Django Admin.
- Testes iniciais dos models criados em `tests/products/test_models.py`.
- Views de listagem e detalhe criadas em `products/views.py`.
- URLs públicas criadas em `products/urls.py` e incluídas em `/produtos/`.
- Templates de catálogo e parcial de card criados.
- Busca, filtro por categoria e paginação inicial implementados.
- Testes do catálogo criados em `tests/products/test_views.py`.
- Direção visual da landing page de referência adaptada aos templates Django.
- Design system inicial aplicado ao layout, catálogo, produto, navegação e rodapé.
- Assets de marca reutilizáveis copiados para `static/images/`.
- Prints da Loja JBS adaptados para home da loja, catálogo com filtros visuais e detalhe de produto.
- Carrinho baseado em sessão criado no app `orders`.
- Adição, atualização e remoção de itens implementadas com proteção CSRF.
- Estoque ativo é validado e a quantidade é limitada no backend.
- Subtotais e total são recalculados a partir dos preços atuais no servidor.
- Contador do carrinho adicionado ao cabeçalho global.
- Testes do carrinho criados em `tests/orders/test_cart.py`.
- `Product` agora diferencia `physical` e `course`, com produtos existentes usando `physical` por padrão.
- O carrinho físico rejeita produtos marcados como curso.
- Migration `products.0002_product_product_type` aplicada.
- Models `Order` e `OrderItem` criados com snapshots de nome, preço e quantidade.
- Checkout físico criado com dados de cliente e endereço de entrega.
- Criação do pedido usa transação e bloqueio das linhas de produto para validar estoque.
- Estoque é reservado ao criar o pedido e pode ser liberado em cancelamento/expiração.
- Integração Mercado Pago preparada com Checkout Pro Orders API, idempotência e webhook.
- Credenciais do Mercado Pago ficam somente no `.env`.
- Instruções para ativação posterior registradas em `docs/mercadopago.md`.
- Dashboard administrativo personalizado em `templates/admin/index.html`.
- Identidade visual do admin em `templates/admin/base_site.html` e
  `static/admin/css/jbs-admin.css`.
- Contexto com indicadores do admin em `core/context_processors.py`.
- Cadastro e autenticação de clientes implementados no app `accounts`.
- Verificação de e-mail e recuperação de senha usando as views nativas do Django.
- Perfil do cliente, endereços salvos e seleção de endereço no checkout.
- Pedidos agora possuem vínculo opcional com o usuário, preservando compras como visitante.
- Área do cliente com histórico de pedidos e gerenciamento de dados/endereço.

## Validações mais recentes

Executadas com as variáveis do `.env` carregadas:

```text
python manage.py check                    OK
python manage.py makemigrations --check   OK
python manage.py migrate                  OK
pytest                                    22 passed
```

Os testes foram executados dentro da rede do Docker Compose, com o PostgreSQL
do serviço `db` ativo. As migrations `accounts.0001` e `orders.0002` também
foram aplicadas no banco do Compose.

## Próximas tarefas detalhadas

1. Configurar SMTP/serviço de e-mail no `.env` e testar verificação e recuperação.
2. Revisar visualmente a área do cliente em desktop e mobile.
3. Preencher credenciais de teste do Mercado Pago no `.env`.
4. Expor uma URL HTTPS/túnel para testar o webhook.
5. Executar uma compra de teste e validar os estados do pedido.
6. Implementar frete real antes da produção.

Não implementar Redis, Celery ou APIs de negócio sem uma etapa específica.
Autenticação e preparação Hotmart já têm implementações locais. O Mercado Pago está preparado, mas depende
de credenciais e teste externo.

## Ordem planejada depois dos products

1. Catálogo público e página de produto.
2. Carrinho baseado em sessão.
3. Classificação entre produto físico e curso.
4. Pedidos físicos.
5. Checkout sem pagamento.
6. Mercado Pago e webhook.
7. Autenticação e contas.
8. Área do cliente.
9. Hotmart e webhooks de cursos.
10. APIs DRF necessárias.
11. Preparação para produção e deploy.

## Regras de retomada

- Ler este arquivo e `AGENTS.md` antes de alterar o projeto.
- Conferir `git status` e preservar mudanças existentes.
- Trabalhar somente na fase atual, salvo solicitação explícita.
- Criar migrations sempre que models forem alterados.
- Atualizar este arquivo ao mudar a fase ou concluir a próxima tarefa.
- Não adicionar dependências ou infraestrutura sem necessidade.

## Preparação de Mercado Pago e Hotmart

Checkout Pro Orders API preservado e auditado; assinatura obrigatória,
validação de referência/total, tratamento de falhas e reembolsos implementados.
App Hotmart com catálogo local, sincronização, Admin e webhook preparada.
As integrações reais dependem de credenciais e validação do Jefferson.
Decisão confirmada pelo usuário: manter compra direta e carrinho para produtos
físicos. A compra direta funciona de forma independente e preserva o carrinho.
Cursos Hotmart continuam com checkout externo.
Ver [auditoria](integrations-audit.md) e [configuração Hotmart](hotmart.md).

Frequência de sincronização Hotmart definida: três vezes ao dia, às 06h, 14h e
22h, no fuso America/Sao_Paulo. Horários documentados; ativação do agendador
pendente do ambiente de hospedagem e das credenciais.

## Regras confirmadas e proteção do checkout

Preço normal da oferta principal Hotmart; cursos de compra única, com parcelas
no checkout externo. Frete adiado para a etapa final. Prazo de compra física:
24 horas. Devolução de mercadoria entregue exige recebimento e conferência antes
da solicitação do reembolso, em operação manual.

CheckoutAttempt vincula o formulário à sessão e a um único pedido, com bloqueio
no PostgreSQL para impedir duplicação por reenvios concorrentes. A rotina
`expire_pending_orders` confere o provedor antes de cancelar ou liberar estoque.
Novas ordens Mercado Pago usam `expiration_time=P1D`. Agendamento de conferência
sugerido a cada 15 minutos; ativação ainda pendente, sem deploy ou novas dependências.
Ver [regras comerciais](commercial-rules.md) e [Mercado Pago](mercadopago.md).
