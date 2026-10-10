# Auditoria e preparação das integrações

## Arquitetura encontrada

O projeto é um monólito Django 5.2 com Templates, DRF reservado em `/api/v1/`,
PostgreSQL, requests e Docker Compose (`web` e `db`). Não foi necessário alterar
requirements, instalar dependências ou introduzir infraestrutura.

`products` tem Category e Product com estoque, preço e classificação
physical/course. Mesmo o curso exige estoque e categoria e não tem identificador,
oferta ou checkout Hotmart. Reutilizá-lo criaria dois contratos comerciais no
mesmo modelo. Foi criada a app `hotmart`, com Course e WebhookEvent independentes,
sem FK para produtos físicos ou pedidos. Produtos antigos do tipo course são
preservados e não são sincronizados por suposição.

`orders` contém Order/OrderItem, carrinho em sessão e serviços transacionais de
criação, reserva e devolução. O snapshot de preço e o UUID do pedido são
adequados. `accounts` mantém o User nativo, perfil/verificação e endereços;
checkout pode associar cliente autenticado e usar endereço salvo. Esses fluxos
não precisaram de refatoração. Hotmart não depende da conta local para comprar.

`payments` já usa Checkout Pro Orders API, apesar de parte da documentação
referir Preferences. Foram preservados API, payload principal, redirects,
referência externa e idempotency key. A documentação passa a apontar para
Orders. Não existe migração de Preferences para outra API neste trabalho.

Settings recebem segredos do ambiente; não havia segredo real no exemplo.
URLs separam loja, Admin e webhooks. Store e Admin continuam carregando CSS
próprio. O novo catálogo reutiliza `.shell`, grid, escala e botões existentes.
O menu Cursos agora aponta para `/cursos/`; filtros antigos ainda funcionam.

## Resultado da auditoria Mercado Pago

| Item | Antes | Trabalho realizado |
| --- | --- | --- |
| Criação | POST /v1/orders com snapshots backend | Preservado; erros de transporte/JSON tratados, checkout validado e total conferido. |
| Relação com Order | provider_order_id e UUID | Preservada; vínculo pelo UUID também recupera criação de resultado incerto. |
| external_reference | UUID | Preservado e confrontado na consulta. |
| Retornos | Sucesso, falha e pendente; não alteram pagamento | Preservados; reembolso agora tem apresentação própria. |
| Webhook | POST e consulta direta | Preservados; falhas de sincronização retornam 503. |
| Assinatura | HMAC, com bypass em DEBUG e ID do corpo como fallback | Secret obrigatório; ID assinado da query, corpo consistente e validação de formato. |
| Consulta | GET /v1/orders/id | Preservada; ID, referência e total validados. |
| Idempotência | UUID remoto, locks e liberação única | Preservada; transições protegem estados de entrega e reembolso. POSTs locais do mesmo formulário agora compartilham CheckoutAttempt e um único pedido. |
| Estados | processed virava pago indiscriminadamente | Reembolso completo e parcial tratados pelo status_detail; nova opção refunded. |
| Segredos | os.getenv e .env ignorado | Preservados; variáveis exigidas documentadas, exemplos vazios. |
| Logs | Sem logs específicos | Logs de estado, falha e HTTP sem credenciais ou payload bruto. |
| Testes | Criação/estoque e um webhook sem assinatura | Mocks HTTP, assinaturas, preço/referência, erros e matriz de estados adicionados. |

Na versão inicial os 88 testes existentes passaram. O teste antigo que dispensava
assinatura em DEBUG foi atualizado para enviar uma assinatura válida e dados
completos do provedor. A mudança do link Cursos também atualiza o teste de menu.

## Compra direta e impacto do carrinho

A compra direta **já existe**: POST `/carrinho/comprar/<produto>/` seleciona
produto e quantidade e abre `/carrinho/checkout/produto/<produto>/<quantidade>/`.
O POST desse checkout coleta cliente/endereço, chama `create_order` e cria o
checkout remoto. Não lê ou esvazia o carrinho para formar o pedido; os testes
comprovam compra sem carrinho e preservação de itens já adicionados. O prefixo
`/carrinho/` é apenas a organização atual das URLs. A integração de pagamento
recebe Order e não depende da origem dos itens.

Decisão confirmada: manter compra direta e carrinho para produtos físicos.
Os dois fluxos existentes continuam disponíveis, sem mudança estrutural.

A avaliação abaixo registra o impacto de uma eventual remoção futura, fora
do escopo aprovado:

1. Manter `buy_now`, `checkout` direto, `create_order`, snapshots, estoque,
   dados do cliente/endereço e integração Mercado Pago.
2. Decidir novos caminhos de compra direta fora de `/carrinho/`; preservar
   compatibilidade dos links antigos conforme a política escolhida. POSTs
   exigem cuidado com redirects que podem perder o corpo.
3. Remover botões Adicionar ao carrinho, contador, drawer e parciais de carrinho
   de base, cards e detalhes; eliminar JS/CSS somente desses componentes.
4. Retirar rotas de adicionar/atualizar/remover, página do carrinho, checkout
   agregado e a ramificação correspondente da view. Depois retirar Cart,
   `create_order_from_cart` e context processor da sessão se não houver usos.
5. Tratar sessões antigas, links e testes que presumem carrinho; atualizar
   navegação, documentação e confirmação de compra direta.
6. Definir como o cliente compra vários produtos: pedidos independentes ou
   manter alguma seleção múltipla. A remoção elimina o atual pedido com vários
   itens, embora OrderItem deva continuar para histórico e snapshots.

A sequência literal Produto > Comprar > Order > Mercado Pago ainda exige os
dados de cliente e entrega dos produtos físicos. O formulário atual resolve
isso. Pular essa tela requer definir endereço obrigatório salvo, confirmação
e tratamento de visitantes. Não criar pedido nem reservar estoque em GET.

Compra direta e carrinho foram mantidos por decisão do usuário. Cursos Hotmart
seguem sempre o checkout externo, sem entrar no carrinho físico.

## Validação e pendências

As migrations criam somente tabelas novas de Hotmart e adicionam choices no
estado Django do Order, sem ALTER TABLE no pedido. O SQL foi inspecionado com
`sqlmigrate`. A migration Hotmart é reversível; revertê-la apaga seus registros,
portanto exige backup em um ambiente com dados reais.

A suíte deve executar `check`, `makemigrations --check --dry-run` e `pytest`
no container existente. Não há credenciais reais ou chamadas reais nos testes.
Os testes de templates cobrem navegação, ações, visibilidade e isolamento do
Admin. Não há ferramenta de navegador disponível neste ambiente para capturar
screenshots desktop/mobile; essa verificação visual permanece pendente.

Jefferson: credenciais e permissões das duas contas, secrets de webhooks,
domínio de teste HTTPS e validação de compra/notificação reais. Para Hotmart,
confirmar cursos, preço normal da oferta principal e parcelamento no checkout. Revisar a copy
e as imagens antes de tornar cada curso visível.

Frequência definida para Hotmart: 06h, 14h e 22h, no fuso America/Sao_Paulo.
A ativação do agendador e o responsável pelo acompanhamento ainda estão pendentes.

Decisões confirmadas: preço normal da oferta principal Hotmart, compra única
com parcelamento no checkout externo, prazo de 24 horas para concluir a compra
e recebimento do produto entregue antes de solicitar reembolso por devolução.
CheckoutAttempt protege reenvios e cliques concorrentes no mesmo formulário.
O frete foi adiado para a etapa final. Ativar e monitorar os agendadores continua
pendente; não foram introduzidos Celery, Redis ou filas.

## Arquivos deste trabalho

Existentes alterados:

- `.env.example`, `config/settings.py`, `config/urls.py`.
- `payments/mercadopago.py`, `payments/services.py`, `payments/views.py`.
- `orders/models.py`, `orders/views.py`.
- `templates/base.html`, `templates/orders/order_confirmation.html`.
- `tests/core/test_navigation.py`, `tests/products/test_views.py`, `tests/orders/test_orders.py`.
- `README.md`, `docs/architecture.md`, `docs/mercadopago.md`, `docs/testing.md`,
  `docs/progress.md`, `docs/deployment-railway.md`.

Criados:

- `hotmart/__init__.py`, `hotmart/apps.py`, `hotmart/models.py`, `hotmart/admin.py`,
  `hotmart/client.py`, `hotmart/services.py`, `hotmart/views.py`, `hotmart/urls.py`.
- `hotmart/management/__init__.py`, `hotmart/management/commands/__init__.py`,
  `hotmart/management/commands/sync_hotmart_courses.py`.
- `hotmart/migrations/__init__.py`, `hotmart/migrations/0001_initial.py`,
  `orders/migrations/0003_alter_order_status.py`.
- `templates/hotmart/course_list.html`, `templates/hotmart/course_detail.html`,
  `templates/hotmart/course_card.html`, `templates/hotmart/purchase_action.html`.
- `tests/hotmart/test_integration.py`, `tests/payments/test_mercadopago.py`.
- `docs/hotmart.md`, `docs/integrations-audit.md`.

Requirements, Docker/Compose, models de produtos/contas e folhas de estilo
existentes foram preservados. Migrations aplicadas somente no PostgreSQL local;
nenhum commit, push ou deploy realizado.

Validação final no serviço web do Compose:

- `python manage.py check`: sem problemas.
- `python manage.py makemigrations --check --dry-run`: nenhuma mudança pendente.
- `pytest`: 147 testes passaram, sem warnings, em 23,73 segundos.
- `sqlmigrate hotmart 0001` e `sqlmigrate orders 0003`: SQL revisado.
- Migrations `hotmart.0001_initial` e `orders.0003_alter_order_status` aplicadas localmente.
- GET real de `/cursos/`: HTTP 200, estado vazio e menu correto, sem CSS do Admin.
- Screenshots desktop/mobile: não executados por falta de ferramenta de navegador.

## Implementação das decisões posteriores

Arquivos de código alterados nesta etapa: `orders/models.py`,
`orders/services.py`, `orders/views.py`, `payments/mercadopago.py`,
`payments/services.py`, `templates/orders/checkout.html`,
`templates/orders/order_confirmation.html` e `static/js/checkout.js`.

Criados `orders/migrations/0004_checkoutattempt.py`,
`orders/management/__init__.py`, `orders/management/commands/__init__.py`,
`orders/management/commands/expire_pending_orders.py`,
`tests/orders/test_checkout_idempotency.py`, `tests/payments/test_expiration.py`
e `docs/commercial-rules.md`. Testes de checkout existentes passaram a obter
o token do formulário antes de enviar; o teste de ofertas Hotmart comprova que
ofertas promocionais alternativas são ignoradas.

README e documentos de arquitetura, testes, progresso, Mercado Pago, Hotmart
e esta auditoria foram atualizados. Frete ficou para a etapa final. Nenhuma
solicitação automática de reembolso foi criada; devoluções físicas continuam
com recebimento/conferência e solicitação manual, conforme a regra registrada.

A migration nova cria somente a tabela de tentativas, com vínculo ao pedido;
o SQL foi revisado e aplicado no PostgreSQL local. Os estáticos foram coletados
localmente para disponibilizar a proteção visual do botão. Não houve deploy,
commit, push, chamadas reais de pagamento ou agendamento ativo.

Validação desta etapa: `check` sem problemas; `makemigrations --check --dry-run`
sem mudanças pendentes; `pytest` com 181 testes aprovados em 24,95 segundos,
sem warnings. `node --check static/js/checkout.js` também passou.
A verificação visual por screenshots continua indisponível neste ambiente.
