# Deploy na Railway

Este documento prepara o deploy, mas não executa login, cria serviços ou publica
o projeto. A aplicação continua sendo um monólito Django com PostgreSQL.

## Arquitetura na Railway

- um serviço web para o container Django;
- um serviço PostgreSQL gerenciado pela Railway;
- armazenamento externo futuro para `media/` e uploads;
- domínio público HTTPS para a loja e para o webhook do Mercado Pago.

O `docker-compose.yml` continua sendo usado apenas no desenvolvimento local.
Não replique o container `db` do Compose na Railway quando o PostgreSQL gerenciado
estiver provisionado.

## Preparar o repositório

1. Envie o repositório para um Git provider conectado à Railway.
2. Confirme que `Dockerfile`, `requirements.txt` e `.dockerignore` estão na raiz.
3. Use o `Dockerfile` existente. O comando padrão inicia:

   ```text
   gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
   ```

4. Configure migrations e coleta de estáticos como etapa de release/pre-deploy:

   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

   Se o plano escolhido não tiver uma etapa pre-deploy, execute esses comandos
   em um shell/one-off command da Railway antes de liberar a nova versão. Não
   coloque migrations no processo principal do Gunicorn.

## Criar os serviços

1. Crie um projeto na Railway.
2. Adicione o repositório como serviço web.
3. Adicione o PostgreSQL da Railway no mesmo projeto.
4. Disponibilize a variável `DATABASE_URL` do PostgreSQL para o serviço web.
5. Use a porta informada pela Railway através da variável `PORT`.
6. Gere um domínio temporário para validar a aplicação antes de configurar o
   domínio oficial.

## Variáveis de ambiente

Configure os valores de produção no serviço web. Nunca copie o `.env` local para
a Railway.

Obrigatórias:

```env
SECRET_KEY=uma-chave-aleatoria-e-longa
DEBUG=False
DATABASE_URL=fornecida-pelo-postgresql-da-railway
ALLOWED_HOSTS=dominio-gerado-ou-oficial
CSRF_TRUSTED_ORIGINS=https://dominio-gerado-ou-oficial
SITE_URL=https://dominio-gerado-ou-oficial
MERCADOPAGO_ACCESS_TOKEN=seu-token-do-ambiente
MERCADOPAGO_WEBHOOK_SECRET=segredo-do-webhook
MERCADOPAGO_API_URL=https://api.mercadopago.com
SECURE_HSTS_PRELOAD=True
```

Depois de adicionar o domínio oficial, atualize `ALLOWED_HOSTS`,
`CSRF_TRUSTED_ORIGINS` e `SITE_URL`. Use apenas hosts conhecidos; não use
`ALLOWED_HOSTS=*`.

O projeto mantém compatibilidade com `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` e
`DJANGO_ALLOWED_HOSTS` para o ambiente local legado, mas a configuração nova
de produção usa os nomes acima.

## Static files e media

O serviço usa WhiteNoise para servir os arquivos coletados em `staticfiles/`.
O comando abaixo deve terminar sem erro:

```bash
python manage.py collectstatic --noinput
```

`media/` permanece com armazenamento local por enquanto. O filesystem de um
serviço Railway pode ser efêmero, portanto não trate uploads permanentes como
arquivos do container. Antes de cadastrar uploads de produção, integrar um
object storage compatível com S3, Cloudinary ou serviço equivalente.

## Mercado Pago

Depois de existir um domínio HTTPS público, configure no Mercado Pago:

```text
https://SEU_DOMINIO/webhooks/mercadopago/
```

O webhook é isento de CSRF porque vem de um serviço externo. Em produção, ele
recusa operar sem `MERCADOPAGO_WEBHOOK_SECRET`, valida a assinatura recebida e
consulta o status da ordem no Mercado Pago antes de atualizar o pedido.

## Admin e teste manual

Crie o primeiro administrador usando um shell/one-off command da Railway:

```bash
python manage.py createsuperuser
```

Valide, nesta ordem:

1. página inicial;
2. `/admin/`;
3. login e recuperação de senha após configurar um e-mail transacional;
4. catálogo e carrinho;
5. checkout de teste do Mercado Pago;
6. recebimento do webhook;
7. arquivos estáticos;
8. logs da aplicação.

## Rollback básico

Se uma versão falhar, interrompa a promoção e volte para o deploy/commit
anterior no histórico do serviço. Depois revise os logs e o estado das
migrations antes de publicar novamente. Migrations destrutivas devem ser
tratadas em uma etapa separada e compatível com rollback.

## Fora deste preparo

Este projeto ainda não configura domínio, DNS, credenciais reais, storage
externo ou serviço Railway. A integração local Hotmart está preparada; sua configuração e validação
com credenciais continuam pendentes. Consulte [hotmart.md](hotmart.md).

## Envio real de e-mail

O backend local apenas escreve mensagens nos logs. Quando o servidor e o
provedor de e-mail estiverem definidos, configure estas variáveis no serviço
web (também se aplicam a hospedagens diferentes da Railway):

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL="JBS Solar <remetente-autorizado@seu-dominio>"
EMAIL_HOST=host-informado-pelo-provedor
EMAIL_PORT=587
EMAIL_HOST_USER=usuario-informado-pelo-provedor
EMAIL_HOST_PASSWORD=credencial-informada-pelo-provedor
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_TIMEOUT=15
```

Use os valores informados pelo provedor. Para uma conexão SSL implícita,
normalmente na porta 465, configure `EMAIL_USE_TLS=False` e
`EMAIL_USE_SSL=True`; não habilite os dois ao mesmo tempo. Autorize o remetente
no provedor e configure os registros DNS que ele solicitar. Guarde a credencial
apenas nas variáveis do servidor.

Reinicie o serviço após configurar. Teste cadastro, confirmação, login e
recuperação de senha com uma conta de teste. Verifique a caixa de entrada e o
spam. Os links devem conter o domínio público HTTPS da loja; acessar por esse
domínio é necessário, pois os links de autenticação usam o host da requisição.
