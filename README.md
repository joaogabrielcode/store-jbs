# JBS Solar Store

Loja online da JBS Solar, construída como um monólito Django. O site é renderizado com Django Templates, usa PostgreSQL para persistência e mantém uma camada preparada para APIs com Django REST Framework.

O projeto já contém catálogo, contas de clientes, carrinho, checkout, pedidos, integração com Mercado Pago e catálogo local de cursos Hotmart. A API versionada está reservada em `/api/v1/` e ainda não possui endpoints implementados.

## Requisitos

- Git
- Docker Engine e Docker Compose
- Ou Python 3.13, um PostgreSQL acessível e um ambiente virtual para executar sem Docker

## Como rodar com Docker

Na raiz do projeto, copie o arquivo de variáveis e ajuste os valores locais:

```bash
cp .env.example .env
```

No mínimo, confira `SECRET_KEY`, `POSTGRES_PASSWORD` e os dados do PostgreSQL. Para checkout, preencha `SITE_URL` (localmente, `http://localhost:8000`). Para o desenvolvimento local, o arquivo de exemplo já aponta o banco para o serviço `db` do Compose.

Suba a aplicação:

```bash
docker compose up --build
```

O serviço `web` executa automaticamente as migrations, coleta os arquivos estáticos e inicia o servidor de desenvolvimento. O PostgreSQL roda no serviço `db`, com os dados persistidos no volume nomeado `postgres_data`.

Acesse:

- Loja e catálogo: <http://localhost:8000/>
- Administração: <http://localhost:8000/admin/>
- Endereço anterior do catálogo (redireciona para a página inicial): <http://localhost:8000/produtos/>
- Cursos sincronizados: <http://localhost:8000/cursos/>
- Conta do cliente: <http://localhost:8000/conta/>
- Carrinho e checkout: <http://localhost:8000/carrinho/>

Para iniciar em segundo plano:

```bash
docker compose up -d --build
```

Para acompanhar os logs ou parar os serviços:

```bash
docker compose logs -f web
docker compose down
```

`docker compose down` mantém o volume do PostgreSQL. Para remover também os dados locais do banco, use `docker compose down -v` somente quando isso for intencional.

Crie um usuário administrador dentro do container quando necessário:

```bash
docker compose exec web python manage.py createsuperuser
```

## Como rodar sem Docker

Esse modo exige um PostgreSQL já instalado e acessível. O host, a porta e as credenciais devem corresponder às variáveis carregadas no ambiente.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
set -a
source .env
set +a
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

O servidor fica disponível em <http://127.0.0.1:8000/>. Nesse modo, `POSTGRES_HOST` normalmente deve apontar para `localhost`, caso o banco esteja rodando na máquina host.

## Variáveis de ambiente

As variáveis ficam em `.env`, que não deve ser versionado. O arquivo `.env.example` contém valores de desenvolvimento e serve como ponto de partida.

| Variável | Uso |
| --- | --- |
| `SECRET_KEY` | Chave secreta do Django. Obrigatória. |
| `DEBUG` | Ativa ou desativa o modo de desenvolvimento. |
| `ALLOWED_HOSTS` | Hosts aceitos pelo Django, separados por vírgula. |
| `CSRF_TRUSTED_ORIGINS` | Origens confiáveis para requisições protegidas por CSRF. |
| `SITE_URL` | URL base usada nos redirecionamentos do checkout. |
| `DATABASE_URL` | Conexão PostgreSQL completa, usada preferencialmente em produção. |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | Configuração do PostgreSQL quando `DATABASE_URL` não é usada. |
| `MERCADOPAGO_ACCESS_TOKEN` | Token usado para criar e consultar ordens no Mercado Pago. |
| `MERCADOPAGO_WEBHOOK_SECRET` | Segredo usado para validar o webhook de pagamentos. |
| `MERCADOPAGO_API_URL` | URL da API do Mercado Pago. |
| `HOTMART_CLIENT_ID`, `HOTMART_CLIENT_SECRET`, `HOTMART_BASIC_AUTH` | Credenciais da API de produtos e ofertas Hotmart. |
| `HOTMART_HOTTOK` | Token de autenticação do webhook Hotmart. |
| `EMAIL_BACKEND` | Backend de e-mail. O padrão local escreve as mensagens no console. |

Em produção, use `DEBUG=False`, uma `SECRET_KEY` própria e hosts e origens explícitos. Consulte [docs/deployment-railway.md](docs/deployment-railway.md) para o preparo na Railway.

## Organização do projeto

```text
config/                 Configurações, URLs e entrypoints ASGI/WSGI
core/                   Página inicial e funcionalidades compartilhadas
products/               Categorias, produtos e catálogo
orders/                 Carrinho, pedidos, checkout e contexto do carrinho
accounts/               Cadastro, autenticação, perfil e endereços
payments/               URLs e integração com o Mercado Pago
hotmart/                Cursos locais, sincronização e eventos Hotmart
templates/              Templates Django por domínio e componentes reutilizáveis
static/                 CSS, JavaScript e imagens versionadas
media/                  Uploads locais de desenvolvimento
tests/                  Testes organizados por app e responsabilidade
docs/                   Arquitetura, desenvolvimento, testes e deploy
manage.py               Interface de comandos do Django
Dockerfile              Imagem do serviço web
docker-compose.yml      Serviços web e PostgreSQL para desenvolvimento
requirements.txt        Dependências Python
```

### Fluxo da aplicação

1. O navegador acessa uma rota definida em `config/urls.py`.
2. O Django encaminha a requisição para a view do app responsável.
3. A view consulta ou altera os dados pelo ORM e aplica as regras no backend.
4. O resultado é renderizado por um template Django ou retornado por uma futura API DRF.

O frontend principal permanece em Django Templates. `templates/base.html` concentra a estrutura compartilhada, `templates/components/` contém parciais reutilizáveis e `static/css/main.css` mantém os estilos da loja. O CSS do Admin fica separado em `static/admin/css/jbs-admin.css`.

### Apps Django

- `core`: página inicial, navegação e context processors compartilhados.
- `products`: `Category` e `Product`, catálogo público e administração de produtos.
- `orders`: carrinho em sessão, `Order`, `OrderItem`, checkout e confirmação de pedidos.
- `accounts`: cadastro, login, recuperação de senha, perfil e endereços.
- `payments`: integração com Mercado Pago, sincronização de pedidos e rota de webhook.
- `hotmart`: catálogo local de cursos, client da API, comando de sincronização e webhook.

As regras de negócio ficam no backend. Preços, subtotais, totais e estoque não devem ser aceitos como informação confiável vinda do navegador.

## Rotas principais

| Prefixo | Responsabilidade |
| --- | --- |
| `/` | Página inicial com catálogo, busca, categorias e paginação |
| `/produtos/` | Redirecionamento permanente para `/`, preservando os parâmetros da URL |
| `/produtos/<slug>/` | Detalhe de produto |
| `/cursos/` | Cursos locais com checkout externo Hotmart |
| `/cursos/<slug>/` | Detalhe de curso |
| `/webhooks/hotmart/` | Webhook Hotmart 2.0.0 autenticado por Hottok |
| `/conta/` | Cadastro, autenticação e área do cliente |
| `/carrinho/` | Carrinho e checkout |
| `/carrinho/comprar/<produto>/` | Início da compra direta por POST |
| `/carrinho/checkout/produto/<produto>/<quantidade>/` | Checkout de um produto, preservando o carrinho |
| `/pedidos/<uuid>/<resultado>/` | Confirmação do pedido |
| `/webhooks/mercadopago/` | Webhook do Mercado Pago |
| `/admin/` | Django Admin |
| `/api/v1/` | Prefixo reservado para a API versionada |

## Testes e verificações

Com o Docker Compose em execução, rode os testes dentro do serviço `web`:

```bash
docker compose exec web pytest
```

Em uma execução sem Docker, carregue o `.env` e confirme que `POSTGRES_HOST` aponta para um PostgreSQL acessível antes de usar:

```bash
pytest
python manage.py check
python manage.py makemigrations --check --dry-run
```

Os testes ficam em `tests/` e são separados por área: `core`, `products`, `orders`, `accounts`, `payments` e `hotmart`. Novas regras de negócio, migrations e endpoints devem receber testes correspondentes.

## Desenvolvimento

Ao alterar models, crie a migration correspondente:

```bash
python manage.py makemigrations
python manage.py migrate
```

Novos endpoints de API devem ficar sob `/api/v1/`. O site continua sendo renderizado com Django Templates. Para detalhes sobre convenções, checkout e organização das features, consulte [docs/development.md](docs/development.md).

Documentação disponível:

- [Arquitetura](docs/architecture.md)
- [Desenvolvimento](docs/development.md)
- [Testes](docs/testing.md)
- [Mercado Pago](docs/mercadopago.md)
- [Deploy na Railway](docs/deployment-railway.md)
- [Roadmap](docs/roadmap.md)

## Integrações de pagamento e cursos

Consulte [Mercado Pago](docs/mercadopago.md), [Hotmart](docs/hotmart.md) e
[auditoria e impacto da compra direta](docs/integrations-audit.md).
Produtos físicos mantêm as duas opções de compra: Comprar agora e carrinho.
A compra direta preserva os itens do carrinho. Ambos usam Mercado Pago, com
Checkout Pro via Orders API. Cursos Hotmart usam somente checkout externo.
A sincronização de cursos
roda com `python manage.py sync_hotmart_courses`; cursos novos ficam ocultos
até revisão no Admin. Páginas de cursos não acessam a API externa.

As [regras comerciais confirmadas](docs/commercial-rules.md) incluem compra
única de cursos, prazo de 24 horas para produtos físicos e devolução operacional.
O checkout protege reenvios do mesmo formulário no PostgreSQL. Para conferir
pedidos vencidos, use `python manage.py expire_pending_orders`; confira a
[documentação de configuração e agendamento](docs/mercadopago.md).
