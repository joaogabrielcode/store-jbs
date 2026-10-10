# Integração Hotmart

Os cursos são sincronizados para o PostgreSQL pelo comando de gerenciamento.
`/cursos/` e `/cursos/<slug>/` consultam somente o banco local. A compra e o
acesso ao conteúdo continuam na Hotmart, sem carrinho, `Order` ou Mercado Pago.

## Configuração

Preencha no ambiente, nunca no código:

```env
HOTMART_CLIENT_ID=
HOTMART_CLIENT_SECRET=
HOTMART_BASIC_AUTH=
HOTMART_HOTTOK=
```

Client ID, Client Secret e Basic vêm de Ferramentas > Credenciais de
desenvolvedor da conta produtora. `HOTMART_BASIC_AUTH` aceita o token Basic
com ou sem o prefixo `Basic `. O Hottok vem da configuração de Webhook e é
independente da autenticação da API.

O client segue o OAuth 2.0 oficial: POST para
`https://api-sec-vlc.hotmart.com/security/oauth/token`, com `grant_type`,
`client_id` e `client_secret` nos parâmetros e Basic no header. O access token
fica apenas na memória do comando e é renovado uma vez por requisição que
receba HTTP 401. Não registrar URLs completas dessas chamadas: a autenticação
oficial inclui o secret nos parâmetros. Os logs da integração mostram somente
contagem e status HTTP, sem headers, payloads, tokens ou dados do comprador.

A listagem usa `GET https://developers.hotmart.com/products/api/v1/products`
com `format=ONLINE_COURSE`. As ofertas vêm de
`GET /products/api/v1/products/<ucode>/offers`. Ambas usam Bearer e paginação
por `page_info.next_page_token`. Não é necessário adicionar SDK ou dependência.

## Sincronização e apresentação

```bash
python manage.py migrate
python manage.py sync_hotmart_courses
```

No ambiente Docker existente:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py sync_hotmart_courses
```

Todas as páginas e ofertas são obtidas e validadas antes da gravação atômica.
Falhas de rede, HTTP, JSON ou dados inválidos encerram o comando com erro e
preservam o catálogo anterior. Curso ausente de uma listagem completa recebe
o marcador local `UNAVAILABLE` e perde o checkout. Esse marcador indica ausência
na sincronização; não é um status inventado para a Hotmart. O registro e os
campos comerciais locais são mantidos. Uma resposta vazia válida desabilita os
checkouts existentes; conferir a conta e suas permissões antes de sincronizar.

`update_or_create` usa `hotmart_id`. Hotmart controla ID, ucode, nome, status,
oferta, preço, moeda e checkout. A oferta escolhida é a principal,
`is_main_offer=true`, em modalidade `PAY_IN_FULL`, para cursos sem assinatura.
Decisão da loja: usar o preço normal da oferta principal, sem selecionar ofertas
promocionais alternativas. A oferta principal precisa estar configurada com o
preço normal na Hotmart; a loja não inventa outro preço se essa oferta for alterada.
O link é exatamente `direct_offer_link_for_creator`, validado como HTTPS no
host `pay.hotmart.com`. Não montamos URL a partir do ID ou ucode. Sem oferta
principal, link ou preço válido, o curso não tem botão de compra. Preço ausente
é `NULL`, nunca um zero fictício.

Os cursos da JBS têm compra única, sem assinatura. O cliente pode pagar à vista
ou parcelar o valor do curso conforme as opções habilitadas na Hotmart. A loja
mostra o preço total e não calcula parcelas, juros ou cobranças mensais. O link
de checkout continua permitindo os meios de pagamento configurados na Hotmart.
Produtos inesperadamente marcados como assinatura ficam sem compra disponível.

O slug inicial inclui o ID para evitar colisões de nomes. O Admin permite
editar slug, URL da imagem de apresentação, descrições, visibilidade, destaque
e ordem. A imagem é uma URL localmente escolhida, usando o padrão existente
do catálogo e evitando dependências de upload. Repetir a sincronização preserva
esses campos. Dados do provedor ficam somente leitura, e a criação acontece
pelo comando, não por preenchimento manual de IDs no Admin.

Cursos novos começam ocultos. Após revisar imagem, descrição, preço e oferta,
marque **visível na loja** no Admin. Cursos visíveis pausados ou sem oferta
continuam na página com compra indisponível. A navegação Cursos aponta para
`/cursos/`. Os antigos `Product` do tipo curso foram preservados; não são
convertidos automaticamente, pois ainda não têm vínculo confiável com a Hotmart.

Frequência definida: três sincronizações por dia, às **06h, 14h e 22h**,
no fuso **America/Sao_Paulo**, com oito horas entre execuções.
O comando manual continua disponível para atualizar uma oferta fora desses horários.

Configure o agendador do ambiente para executar `python manage.py sync_hotmart_courses`
nesses horários. Em um agendador compatível com cron, a expressão é:

```text
0 6,14,22 * * *
```

Essa expressão pressupõe que o agendador esteja configurado no fuso
America/Sao_Paulo. O TIME_ZONE do Django não configura o fuso do agendador.
A ativação ainda depende da escolha do ambiente de hospedagem, das credenciais
e do responsável por acompanhar erros. Nenhuma tarefa foi instalada ou ativada
no servidor local. Não há filas, Celery ou Redis.

Se uma execução falhar, o catálogo anterior permanece disponível e o erro deve
ser acompanhado. Uma atualização bem-sucedida pode ficar até oito horas atrás
de uma mudança na Hotmart; falhas podem prolongar esse intervalo. A Hotmart
confirma o preço final em seu checkout.

## Webhook

Configure na conta Hotmart a versão **2.0.0**, com endereço público HTTPS:

```text
POST /webhooks/hotmart/
```

O mecanismo oficial é o header `X-HOTMART-HOTTOK`, comparado em tempo constante
com `HOTMART_HOTTOK`. Não há uma assinatura HMAC inventada. Sem secret configurado
o endpoint responde 503, inclusive em DEBUG. Token inválido recebe 403; JSON,
versão ou campos inválidos recebem 400; evento válido recebe 200.

O processamento guarda uma linha por ID único do evento, protegida também pela
restrição no banco. Registra nome do evento, ID do produto, transação, status
da compra, data de criação e recebimento. Reenvios não duplicam processamento;
eventos fora de ordem são preservados como histórico, sem sobrescrever um
estado agregado. Não persiste o payload bruto nem dados do comprador. O Admin
permite consultar esses eventos somente para leitura.

Um evento de compra não significa que o produto foi ativado, pausado ou teve
preço atualizado. Por isso não altera `Course`, nem cria `Order`, usuários ou
matrículas. Entrega e acesso pertencem à Hotmart. Essa recepção é suficiente
para o catálogo com checkout externo solicitado; automações de matrícula ou
conciliação financeira local exigiriam um escopo próprio.

## Testar em desenvolvimento

```bash
docker compose exec web pytest tests/hotmart
```

Os testes usam mocks e credenciais fictícias; não acessam a API real. Validam
paginação de produtos/ofertas, renovação de token, timeouts, falhas sem gravação
parcial, preço, URLs, preservação editorial, Admin, visibilidade e idempotência.

Com credenciais de teste autorizadas da Hotmart, configure um túnel HTTPS e use
o envio de teste da ferramenta de Webhook. Nunca exponha o Hottok no navegador.
O PostgreSQL local precisa das migrations; as páginas funcionam sem credenciais,
com catálogo vazio até a primeira sincronização.

## Antes da produção

Jefferson precisa confirmar a conta produtora, permissões da API, credenciais,
Hottok e cursos. Conferir se a oferta principal contém o preço normal, se o
parcelamento está habilitado no checkout e se há produtos em formato `VIDEOS`,
fora do filtro atual. Não há cursos recorrentes no escopo confirmado. Conferir o link direto
retornado por cada oferta e a moeda. Configurar webhook e testar seu envio real,
reenvios e recusas. Ativar os três horários definidos e escolher o responsável
pelo monitoramento de falhas, revisão de cursos novos e retenção dos eventos. Usar HTTPS, ambiente sem
DEBUG e backups do banco. A configuração não equivale a um deploy.

Referências oficiais consultadas:

- [Autenticação](https://developers.hotmart.com/docs/pt-BR/start/app-auth/)
- [Produtos](https://developers.hotmart.com/docs/pt-BR/v1/product/product-list/)
- [Ofertas e link direto](https://developers.hotmart.com/docs/pt-BR/v1/product/product-offers/)
- [Webhook de compras 2.0.0](https://developers.hotmart.com/docs/pt-BR/2.0.0/webhook/purchase-webhook/)
- [Hottok no header](https://developers.hotmart.com/docs/pt-BR/tutorials/use-webhook-for-subscriptions/)
