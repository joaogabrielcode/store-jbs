# Desenvolvimento

## Executar o projeto

```bash
cp .env.example .env
docker compose up
```

O serviço web executa migrations e coleta estáticos ao iniciar. Para desenvolvimento local sem Docker, instale `requirements.txt`, exporte as variáveis do `.env` e use `python manage.py runserver`.

No ambiente de produção, o Dockerfile usa Gunicorn. Migrations e coleta de
estáticos devem ser executadas como etapa de release/pre-deploy. Consulte
`docs/deployment-railway.md` para a configuração da Railway.

## Convenções

- O frontend principal usa Django Templates.
- O CSS do storefront fica isolado sob `.store-app`; o CSS do Django Admin fica
  em `static/admin/css/jbs-admin.css` e só é carregado por templates do admin.
  Não compartilhar stylesheets entre os dois contextos nem adicionar seletores
  globais que possam vazar entre loja e admin.
- A API futura usa DRF sob `/api/v1/`.
- Views devem permanecer simples; regras importantes ficam no backend.
- Use `DecimalField`/`Decimal` para valores monetários.
- Use transações em operações críticas de pedidos e pagamentos.
- Crie `services.py` e `selectors.py` somente quando houver complexidade real.
- Não implemente fases futuras sem solicitação explícita.

## Como adicionar uma feature

1. Confirme o escopo e o app responsável.
2. Modele a regra no backend antes de criar a interface.
3. Altere models somente com migration correspondente.
4. Reutilize templates e crie parciais para elementos repetidos.
5. Adicione testes para regras críticas e atualize a documentação se a arquitetura mudar.
6. Execute as verificações relevantes antes de finalizar.

## Organização do projeto

O projeto é um monólito Django modular. `config/` concentra configurações e
rotas; `core/` contém funcionalidades compartilhadas; `products/`, `orders/`,
`accounts/` e `payments/` mantêm responsabilidades de domínio separadas.
Templates reutilizáveis ficam em `templates/`, arquivos versionados em `static/`
e uploads locais de desenvolvimento em `media/`. O filesystem de produção pode
ser efêmero; uploads permanentes exigem object storage externo.

Use `services.py` apenas para operações de negócio que realmente exijam uma
camada própria e `selectors.py` apenas para consultas complexas reutilizadas.
CRUD simples deve continuar nas abstrações convencionais do Django. O site
principal continua server-rendered com Django Templates; APIs novas devem ficar
sob `/api/v1/` e só devem ser criadas quando houver necessidade real.

O Compose fornece os serviços `web` e `db`, com o volume nomeado
`postgres_data`. Segredos ficam no `.env`, que não deve ser versionado.

## Checkout de produtos físicos

O checkout em `/carrinho/checkout/` cria pedidos físicos com endereço, reserva
estoque em uma transação e redireciona para o Mercado Pago. Configure as
variáveis `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_WEBHOOK_SECRET` e
`SITE_URL` no `.env`. O webhook deve apontar para
`/webhooks/mercadopago/` e somente confirmar o pedido após consultar o status
no Mercado Pago.

## Skills selecionadas

As skills locais selecionadas estão em `.agents/skills/` e são descritas no
`AGENTS.md`. Elas cobrem Django/ORM, segurança, testes/TDD, Python, PostgreSQL,
APIs, migrations e Docker. A skill global `Django Framework` complementa esse
conjunto. Skills de FastAPI, Flask, Celery, Redis, Kubernetes e GraphQL não
fazem parte desta fase.

## Cadastro e recuperação de senha no ambiente local

O cadastro em `/conta/cadastro/` exige confirmação do e-mail antes do login.
Com o backend de console padrão, as mensagens não chegam à caixa de entrada.
Para testar:

1. Cadastre uma conta com um e-mail ainda não utilizado.
2. Execute `docker compose logs --tail=100 web` e copie o link de confirmação
   da mensagem. Abra-o no navegador que acessa a loja.
3. Entre em `/conta/entrar/`; o login leva para `/conta/minha-conta/` ou para
   a página protegida que você tentou acessar.
4. Clique em **Esqueci minha senha**, informe o e-mail e copie o link de
   recuperação dos logs. Defina uma nova senha e entre novamente.

Os links usam o host pelo qual a loja foi acessada. O link de recuperação
expira conforme `PASSWORD_RESET_TIMEOUT` do Django e deixa de funcionar após
alterar a senha. A recuperação não dispensa a confirmação do e-mail.
Por privacidade, um e-mail inexistente recebe a mesma tela de confirmação,
mas não gera mensagem.

As credenciais SMTP são opcionais no desenvolvimento. Consulte
`docs/deployment-railway.md` para ativar o envio real quando houver servidor.
Não compartilhe logs que contenham links de confirmação ou recuperação.
