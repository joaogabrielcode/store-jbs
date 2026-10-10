# Arquitetura do sistema

Este documento descreve como a JBS Solar Store está organizada hoje, quais decisões orientam o desenvolvimento e onde cada responsabilidade deve ficar. A referência principal é o código existente no repositório. Funcionalidades reservadas para fases futuras aparecem identificadas como futuras.

## 1. Visão geral

A aplicação é um monólito Django modular. Todos os domínios executam no mesmo processo web e compartilham o mesmo banco PostgreSQL, mas cada app Django mantém uma responsabilidade própria.

```text
Navegador
   |
   v
Django URLs
   |
   +--> Views de páginas --> ORM Django --> PostgreSQL
   |          |
   |          +--> Django Templates --> HTML
   |
   +--> Django Admin
   |
   +--> Webhook Mercado Pago --> payments/orders --> PostgreSQL
   |
   +--> /api/v1/ (prefixo reservado para DRF)
```

O frontend principal é renderizado no servidor com Django Templates. JavaScript é usado para interações pontuais, como o drawer do carrinho, sem transformar a loja em uma aplicação SPA. Django REST Framework está instalado para APIs futuras, mas `/api/v1/` ainda não possui endpoints implementados.

A arquitetura evita, nesta fase, microservices, filas, Redis, Celery, Kafka, GraphQL e Kubernetes. Essas tecnologias não fazem parte do fluxo atual e só devem ser adicionadas se uma necessidade concreta for aprovada.

## 2. Camadas e responsabilidades

### Configuração e entrada da aplicação

`config/` é o projeto Django. Ele não representa um domínio de negócio.

- `config/settings.py`: configurações de apps, middleware, templates, banco, arquivos estáticos, segurança, e-mail e Mercado Pago.
- `config/urls.py`: roteamento principal da loja, Admin, webhook e API.
- `config/api_urls.py`: ponto de entrada da API, atualmente com o prefixo `/api/v1/` reservado.
- `config/wsgi.py`: entrada WSGI usada pelo Gunicorn.
- `config/asgi.py`: entrada ASGI do Django.
- `manage.py`: comandos administrativos e de desenvolvimento.

### Apps de domínio

Cada app contém modelos, migrations, views, URLs, formulários e administração relacionados ao próprio domínio. As dependências entre apps devem apontar para uma responsabilidade clara e evitar importações circulares.

| App | Responsabilidade atual |
| --- | --- |
| `core` | Página inicial, navegação e context processors compartilhados. |
| `products` | Categorias, produtos, catálogo público e administração de produtos. |
| `orders` | Carrinho em sessão, pedidos, itens, checkout, estoque e confirmação. |
| `accounts` | Cadastro, autenticação, perfil, verificação de e-mail, recuperação de senha e endereços. |
| `payments` | Integração HTTP com Mercado Pago e exposição da rota de webhook. |
| `hotmart` | Cursos locais, sincronização de produtos/ofertas e recepção de eventos autenticados. |

O app `payments` não possui modelos próprios. O pedido continua sendo responsabilidade de `orders`; o provedor de pagamento é uma integração externa que atualiza esse pedido.

## 3. Organização dos diretórios

```text
config/                 Configuração e roteamento do projeto Django
core/                   Funcionalidades compartilhadas
products/               Domínio de catálogo
orders/                 Carrinho, pedidos e checkout
accounts/               Usuários, perfis e endereços
payments/               Integração com Mercado Pago
hotmart/                Cursos locais, sincronização e eventos Hotmart
templates/              Templates globais, por app e componentes reutilizáveis
static/                 CSS, JavaScript e imagens versionadas
media/                  Arquivos enviados localmente durante o desenvolvimento
tests/                  Testes organizados por app
docs/                   Documentação técnica e de produto
Dockerfile              Imagem do serviço web
docker-compose.yml      Ambiente local com web e PostgreSQL
requirements.txt        Dependências Python
```

Dentro dos apps, o padrão atual segue as convenções do Django: `models.py` para persistência, `views.py` para entrada HTTP, `forms.py` para validação de formulários, `urls.py` para rotas, `admin.py` para o Admin e `migrations/` para evolução do banco.

`services.py` deve ser usado quando uma operação de negócio atravessar mais de uma entidade ou exigir transação. Hoje `orders/services.py` concentra a criação do pedido, as transições importantes de status e a devolução de estoque. `payments/services.py` coordena a consulta ao Mercado Pago e a sincronização com o pedido local. Um `selectors.py` só deve ser criado quando consultas complexas forem reutilizadas; CRUD simples deve continuar no ORM usado pela view.

## 4. Fluxo de uma requisição

A página inicial `/` reutiliza a view `products.views.product_list` e o template
`products/product_list.html`, com busca, categorias e paginação. O endereço
anterior `/produtos/` redireciona permanentemente para `/`, preservando os
parâmetros da URL. Os detalhes continuam em `/produtos/<slug>/`.

O menu da loja possui Início, Kits solares, Softwares, Cursos, Equipamentos e
Documentos, nessa ordem. As categorias do menu são definidas em
`products/catalog.py` e ficam visíveis mesmo sem produtos. Softwares reutiliza o
destaque laranja do cabeçalho. A seleção usa `?categoria=<slug>` no catálogo.

Cursos aponta para `/cursos/`, catálogo local sincronizado da Hotmart.
Kits solares, Softwares e Documentos filtram a categoria com o slug
correspondente (`kits-solares`, `softwares` e `documentos`). O filtro legado
`?categoria=cursos` continua acessível para os Product existentes. Equipamentos
reúne produtos do tipo físico nas demais categorias ativas, incluindo a categoria
`equipamentos`, painéis, inversores e carregadores. Produtos das quatro categorias
separadas e produtos do tipo curso não entram nesse grupo. A busca e a paginação
continuam sendo aplicadas sobre o filtro selecionado.

Em cada ambiente, cadastre as categorias do menu no Admin com esses slugs antes
de associar produtos a elas. O menu também funciona antes do cadastro, mostrando
o estado vazio nas categorias sem produtos. As categorias específicas existentes
continuam disponíveis na lateral do catálogo.

1. O navegador acessa uma URL pública, a área da conta, o carrinho ou o Admin. O Mercado Pago acessa separadamente a rota de webhook.
2. `config/urls.py` encaminha a URL para o app responsável.
3. A view valida a entrada com um `Form`, consulta o ORM e executa a regra necessária.
4. Para páginas HTML, a view chama `render()` com um template de `templates/`.
5. Para ações de redirecionamento, a view usa `redirect()` após concluir a operação.
6. Para o carrinho assíncrono, a view retorna JSON com HTML renderizado pelo parcial `orders/partials/cart_drawer_content.html`.
7. O webhook é validado em `payments/views.py` e a sincronização com o provedor fica em `payments/services.py`.
8. A resposta volta ao navegador ou ao provedor externo.

Os context processors fornecem dados compartilhados aos templates:

- `orders.context_processors.cart_summary`: itens, quantidade e total do carrinho.
- `core.context_processors.store_navigation`: categorias fixas do menu principal.
- `core.context_processors.admin_dashboard`: estatísticas exibidas no Admin para usuários staff.

Esses processadores devem permanecer leves. Consultas agregadas ou específicas de uma página devem continuar na view para evitar consultas desnecessárias em todas as requisições.

## 5. Persistência e modelo de dados

O banco oficial é PostgreSQL. A configuração aceita `DATABASE_URL`, usada preferencialmente em ambientes de deploy, ou as variáveis separadas `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` e `POSTGRES_PORT`.

### Catálogo

`products` possui:

- `Category`: nome, slug e status ativo.
- `Product`: categoria protegida, nome, slug, descrição, tipo, preço, estoque, imagem, status e timestamps.

Produtos usam `DecimalField` para valores monetários. O banco também aplica constraints para impedir preço e estoque negativos. Categorias não podem ser excluídas enquanto tiverem produtos relacionados, por causa do `on_delete=PROTECT`.

### Clientes

`accounts` usa o usuário padrão do Django e adiciona:

- `CustomerProfile`: telefone, verificação de e-mail e data de aceite dos termos.
- `CustomerAddress`: endereços associados ao usuário, com indicação de endereço principal.

Existe uma constraint condicional que permite apenas um endereço principal por usuário.

### Pedidos

`orders` possui:

- `Order`: usuário opcional, status interno, provedor de pagamento, dados do cliente e entrega, subtotal, frete, total e identificadores do Mercado Pago.
- `OrderItem`: produto relacionado quando disponível e snapshot do nome, preço unitário, quantidade e subtotal no momento da compra.

O snapshot em `OrderItem` preserva os dados comerciais do pedido mesmo que o produto seja alterado depois. O produto pode ser definido como nulo quando for removido, mas o item mantém nome e preço históricos.

Os status internos do pedido são `pending_payment`, `paid`, `processing`, `shipped`, `delivered` e `canceled`. O provedor também mantém um status externo em `provider_status`; os dois campos têm funções diferentes e não devem ser tratados como equivalentes sem uma regra explícita.

## 6. Carrinho, estoque e checkout

O carrinho é armazenado na sessão do Django sob a chave `cart`. Ele guarda IDs de produtos e quantidades, não preços. Ao ler o carrinho, o sistema consulta novamente os produtos ativos, verifica a categoria e limita a quantidade ao estoque atual.

O checkout segue este fluxo:

1. A view confirma que o carrinho possui produtos físicos disponíveis.
2. `CheckoutForm` valida os dados do cliente e do endereço.
3. `create_order_from_cart()` encaminha os itens para `create_order()`, que abre
   uma transação atômica compartilhada pelos dois fluxos de compra.
4. Os produtos são buscados com `select_for_update()`, bloqueando as linhas durante a reserva.
5. Preços, subtotais e total são calculados no servidor com `Decimal`.
6. `Order` e `OrderItem` são persistidos com os valores calculados.
7. O estoque é reduzido e o pedido é vinculado à tentativa de checkout.
8. O pedido é enviado ao Mercado Pago.
9. Os identificadores e a URL de checkout retornados pelo provedor são gravados no pedido.
10. No fluxo agregado, o carrinho é limpo após a criação remota bem-sucedida.

Se o provedor recusar explicitamente a criação, `cancel_order()` devolve o estoque
e cancela o pedido. `stock_released_at` impede devolução duplicada. Erros de
transporte, HTTP 5xx e respostas incompletas mantêm o pedido e a reserva pendentes
para conciliação, pois a ordem pode ter sido aceita no provedor.

### Compra direta

O botão Comprar agora usa `POST /carrinho/comprar/<produto>/`, com CSRF e validação
de quantidade, disponibilidade e tipo físico. No catálogo, inicia com uma unidade;
na página do produto, usa a quantidade escolhida. A resposta encaminha para
`/carrinho/checkout/produto/<produto>/<quantidade>/`, onde o checkout existente
mostra somente esse item e seus dados de entrega.

O produto e a quantidade ficam no endereço do checkout, sem substituir dados do
carrinho na sessão. Isso permite abrir compras diretas diferentes em abas separadas.
GET apenas exibe o resumo; o POST do formulário valida os dados e chama
`create_order()` com um único produto. Preço e estoque são consultados no servidor,
com bloqueio de linha e reserva de estoque, antes do envio ao Mercado Pago.

A compra direta não limpa nem adiciona itens ao carrinho. Uma recusa explícita
do Mercado Pago cancela o pedido e devolve o estoque; um resultado inconclusivo
mantém a reserva para conciliação. Produtos do tipo curso continuam fora do checkout físico. Os botões de
compra ficam desativados quando não há estoque.

Preços, totais, disponibilidade e quantidade válida são sempre recalculados no backend. Dados enviados pelo navegador servem como entrada para validação, nunca como fonte de confiança comercial.

## 7. Integração com Mercado Pago

`payments/mercadopago.py` isola as chamadas HTTP ao provedor. O módulo cria e consulta ordens usando:

- `MERCADOPAGO_ACCESS_TOKEN` para autenticação;
- `MERCADOPAGO_API_URL` como base da API;
- `X-Idempotency-Key` com o número do pedido ao criar a ordem;
- timeout de 15 segundos nas chamadas externas.

O webhook fica em `/webhooks/mercadopago/`. A view:

1. recebe apenas `POST`;
2. lê o ID assinado da query string e verifica a correspondência com o corpo;
3. exige `MERCADOPAGO_WEBHOOK_SECRET` em todos os ambientes;
4. valida a assinatura HMAC;
5. consulta a API e confere ID, referência externa e total;
6. atualiza o pedido dentro de uma transação com bloqueio da linha;
7. aplica pagamento, cancelamento ou reembolso conforme status e detalhe oficiais,
   preservando os estados de preparação e entrega.

O webhook é isento de CSRF porque é chamado por um serviço externo, mas a assinatura e a consulta ao provedor são necessárias para evitar confiar no conteúdo recebido diretamente. O controller HTTP fica em `payments/views.py`; `orders` fornece as operações de domínio que alteram o pedido.

## 8. Templates, CSS e JavaScript

O layout compartilhado está em `templates/base.html`. Templates de domínio ficam em diretórios como `templates/products/`, `templates/orders/` e `templates/accounts/`. Elementos repetidos devem virar parciais em `templates/components/` ou no diretório do app.

O CSS da loja fica em `static/css/main.css` e deve ser escopado ao contexto `.store-app`. O Admin usa `static/admin/css/jbs-admin.css` e seus templates próprios. Os dois contextos não devem compartilhar folhas de estilo nem seletores globais.

O JavaScript em `static/js/` atende interações do storefront. Ele não substitui as validações do servidor. Uma ação iniciada por JavaScript deve continuar funcionando com as regras de autorização, CSRF, estoque e cálculo aplicadas no backend.

## 9. Configurações de execução

### Desenvolvimento com Docker

O `docker-compose.yml` cria:

- `db`: PostgreSQL 16 Alpine, com healthcheck e volume `postgres_data`;
- `web`: imagem Python 3.13, código montado em `/app` e porta `8000` publicada.

Ao iniciar, o serviço web executa `migrate`, `collectstatic` e `runserver`. O host do banco dentro da rede Compose é `db`.

### Imagem e produção

O `Dockerfile` instala as dependências, copia o projeto e usa Gunicorn com `config.wsgi:application`. Em produção, migrations e coleta de arquivos estáticos devem ocorrer em uma etapa de release ou pre-deploy, antes de liberar a nova versão.

WhiteNoise serve os arquivos estáticos coletados em `STATIC_ROOT`. `media/` usa armazenamento local atualmente; em ambientes com filesystem efêmero, uploads permanentes exigem object storage externo.

### Segurança por configuração

Quando `DEBUG=False`, o projeto ativa redirecionamento HTTPS, cookies seguros, HSTS, `X-Frame-Options: DENY`, `SECURE_CONTENT_TYPE_NOSNIFF` e política de referrer. `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` devem conter somente hosts conhecidos.

Segredos não ficam no código nem no Git. O `.env.example` contém apenas valores de referência; credenciais reais devem ser configuradas no ambiente de execução.

## 10. Decisões de organização aplicadas

Esta revisão manteve o monólito, os apps existentes, os templates, o PostgreSQL, o Admin, o DRF reservado e o Docker Compose. As mudanças estruturais foram pequenas:

- o webhook foi movido de `orders/views.py` para `payments/views.py`, porque valida uma notificação externa e pertence ao limite da integração de pagamentos;
- a sincronização com o Mercado Pago foi concentrada em `payments/services.py`, mantendo a chamada HTTP e a atualização local separadas do controller;
- `orders/services.py` passou a centralizar as transições usadas hoje: `mark_order_as_paid()` e `cancel_order()`;
- `cancel_order()` mantém a devolução de estoque idempotente e `release_order_stock()` continua disponível como nome compatível para essa operação;
- a exclusão de endereço e a promoção de um substituto passaram a ocorrer na mesma transação;
- `config/settings.py` não foi dividido em vários módulos. A configuração atual já diferencia desenvolvimento e produção por variáveis de ambiente, e a divisão traria mais pontos de entrada sem benefício proporcional neste tamanho de projeto.

Não foram criados repositories, classes base, `selectors.py`, state machine,
custom user ou endpoints DRF. A integração Hotmart agora mantém modelos próprios
para catálogo externo e eventos, conforme a seção de integração abaixo.

## 11. Testes, migrations e evolução

Os testes usam `pytest` e `pytest-django`, com `DJANGO_SETTINGS_MODULE=config.settings` definido em `pytest.ini`. A organização atual é:

- `tests/core/`: navegação e páginas compartilhadas;
- `tests/products/`: modelos e catálogo;
- `tests/orders/`: carrinho, estoque, checkout e pedidos;
- `tests/accounts/`: cadastro, perfil e endereços;
- `tests/payments/`: integração Mercado Pago com mocks;
- `tests/hotmart/`: sincronização, páginas, Admin e webhooks com mocks.

Alterações em models exigem migration. Antes de concluir uma mudança, execute:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
pytest
```

Regras críticas devem ter testes: cálculo de valores, reserva e devolução idempotente de estoque, preço calculado no backend, autorização de dados privados, verificação de assinatura, consulta do status externo e transições de status.

Novas APIs devem ser criadas apenas quando houver necessidade concreta e sempre sob `/api/v1/`, com serializers, autenticação, permissões, paginação e testes do contrato. O site principal continua usando Django Templates.

## 12. Regras para novas features

1. Defina o app responsável antes de alterar o código.
2. Modele a regra no backend antes de construir a interface.
3. Use `Form` ou serializer para validar entradas.
4. Use `Decimal` para valores monetários e transações para operações críticas.
5. Crie migrations para alterações persistentes.
6. Reutilize templates e componentes existentes.
7. Mantenha o CSS da loja separado do Admin.
8. Adicione testes para a regra nova e para os efeitos sobre estoque, pedidos ou autenticação.
9. Atualize este documento quando uma decisão estrutural mudar.

Não crie uma nova camada, dependência ou serviço apenas para seguir um padrão abstrato. A estrutura deve crescer junto com a complexidade real do domínio.

## Integração Hotmart e confirmação de pagamentos

`hotmart` mantém Course e WebhookEvent no mesmo PostgreSQL do monólito, sem
reutilizar Product ou Order para checkout externo. O comando de sincronização
consulta produtos e ofertas, enquanto `/cursos/` consulta somente o banco.
Eventos autenticados ficam como histórico idempotente; não alteram pedidos
físicos nem matrículas. Consulte [Hotmart](hotmart.md).

`payments` mantém Checkout Pro via Orders API. O webhook exige assinatura,
consulta ID/referência/total e aplica estados de pagamento e reembolso.
Consulte [Mercado Pago](mercadopago.md) e [auditoria](integrations-audit.md).
A compra direta já funciona sem carrinho; o carrinho permanece disponível.

## Tentativas de checkout e prazo de pagamento

`orders.CheckoutAttempt` guarda o token do formulário, sessão, URL, quantidades,
data e vínculo único com Order. A tentativa é bloqueada durante a criação local
e vinculada na mesma transação da reserva. Reenvios reutilizam esse pedido.
A chamada ao Mercado Pago acontece após o commit; outra requisição durante essa
chamada acessa a confirmação local, sem criar um segundo pagamento. Formulários
novos podem iniciar novas compras intencionais. O carrinho é limpo após criação
bem-sucedida do checkout remoto.

O checkout remoto recebe validade de um dia. `expire_pending_orders` verifica
pedidos locais com 24 horas ou mais, consulta e, quando permitido, cancela no
provedor e consulta novamente. A reserva só é liberada após confirmação segura.
Não há agendador embutido nem serviço novo; o comando pode ser agendado no
ambiente. Regras e limitações estão em [mercadopago.md](mercadopago.md).
