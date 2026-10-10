# Mercado Pago

A integração existente usa **Checkout Pro via Orders API** (`/v1/orders`).
Foi preservada. Não havia integração Preferences para migrar. A auditoria está
em [integrations-audit.md](integrations-audit.md).

## Configuração

As variáveis necessárias estão no `.env.example`, sem credenciais:

```env
MERCADOPAGO_ACCESS_TOKEN=
MERCADOPAGO_WEBHOOK_SECRET=
MERCADOPAGO_API_URL=https://api.mercadopago.com
SITE_URL=
```

Obtenha o Access Token de teste da aplicação da JBS Solar e a chave secreta
em Webhooks > Configurar notificações. Preencha somente o `.env` ou as variáveis
do ambiente. `SITE_URL` deve ser a URL base da loja sem barra final; use
`http://localhost:8000` apenas em desenvolvimento. Para retorno e webhook reais,
use um endereço HTTPS público, por exemplo um túnel autorizado de desenvolvimento.
Nunca inserir tokens em templates, código ou logs.

## Checkout e confirmação

Carrinho e compra direta usam `orders.services.create_order`: bloqueiam os
produtos, conferem disponibilidade e estoque, calculam o preço do banco,
salvam snapshots dos itens e reservam estoque na mesma transação. O pedido usa
UUID em `external_reference` e `X-Idempotency-Key`. Repetir a criação remota
para esse mesmo pedido usa a mesma chave. Cada formulário agora recebe um token
emitido no servidor e registrado em CheckoutAttempt, ligado à sessão, URL e
itens. A linha da tentativa é bloqueada para vincular um único Order. Reenvios
ou POSTs concorrentes do mesmo formulário reutilizam esse pedido, sem nova
reserva ou segunda chamada de criação ao provedor. Abrir um novo formulário
permite uma nova compra intencional; tentativas distintas não são unificadas.

O total remoto deve corresponder à soma dos itens. O frete atual é zero;
quando for implementado frete real, seu valor deve ser representado de acordo
com a API, sem simplesmente alterar `total_amount`. A integração bloqueia
criação com total divergente. O retorno exige ID e URL de checkout HTTPS válida.

As URLs de retorno são `/pedidos/<uuid>/sucesso/`, `/falha/` e `/pendente/`.
Elas só mostram o estado local; parâmetros do navegador não aprovam pagamentos.
A consulta ao provedor ocorre no webhook, antes de alterar o pedido.

Uma recusa explícita de criação cancela o pedido e devolve a reserva uma vez.
Timeout, erro de rede, HTTP 5xx ou resposta incompleta são inconclusivos: o
pedido permanece pendente e com estoque reservado, pois pode ter sido aceito
no provedor. Não iniciar outra compra antes da conciliação. Um webhook pode
vincular o ID remoto por `external_reference`, mesmo quando a resposta de criação
não chegou. Se não houver notificação, localizar a ordem no painel do provedor,
consultá-la e conciliar antes de cancelar ou tentar novamente. Reenviar o mesmo
formulário inconclusivo mostra o pedido existente, sem iniciar outro pagamento.
O carrinho é limpo apenas quando o checkout remoto é criado com sucesso.

## Webhook e estados

No painel, selecionar o evento **Order (Mercado Pago)** e configurar:

```text
POST https://<dominio-da-loja>/webhooks/mercadopago/
```

O endpoint usa `data.id` da query string, `x-request-id`, `ts` e `v1` do
header `x-signature`. O manifesto HMAC-SHA256 preserva o ID exatamente como
recebido, conforme o validador do SDK oficial atual. O ID no corpo deve
corresponder à query. Não há bypass em DEBUG. Sem secret: 503; assinatura
inválida: 403; formato inválido: 400. Não há janela temporal arbitrária para
recusar reenvios; cada evento assinado exige nova consulta à API.

A consulta autenticada `GET /v1/orders/<id>` deve retornar ID, referência e
`total_amount` iguais ao pedido local. Uma consulta falha, divergente ou sem
pedido correspondente retorna 503 para permitir nova tentativa de entrega.
Somente a sincronização concluída retorna 200. A implementação é síncrona,
com timeout de 15 segundos na consulta, dentro dos 22 segundos de confirmação
documentados pelo provedor em condições normais. Acompanhar latência e falhas.

| Orders API | Pedido local e estoque |
| --- | --- |
| `created`, `processing`, `action_required` | Continua aguardando; reserva mantida. |
| `processed` + `accredited` | Pago; reenvios preservam preparação, envio e entrega. |
| `failed`, `canceled`, `expired` | Cancela e libera estoque uma vez se ainda pendente. |
| `refunded` ou `processed` + `refunded` | Reembolsado; não retorna mercadoria automaticamente ao estoque. |
| `processed` + `partially_refunded` | Permanece pago; detalhe persistido para conferência manual. |

`pending`, `approved`, `rejected` e `cancelled` são nomes usados em outros
recursos ou descrições do pagamento; não devem ser misturados com os estados
da Orders API. O processamento usa os estados oficiais dessa API.

Uma aprovação recebida para pedido já cancelado ou reembolsado gera erro de
conciliação e não ressuscita a reserva. Eventos não regridem a preparação/envio
para pago nem liberam estoque de pedido já pago por uma falha posterior. O
campo `provider_status` guarda `status:status_detail` quando há detalhe. Logs
mostram UUID do pedido, estado e códigos HTTP, sem token ou payload do comprador.

## Desenvolvimento e produção

```bash
docker compose exec web pytest tests/payments tests/orders
```

Os testes usam mocks, assinatura calculada com secret fictício e PostgreSQL de
teste. Para validar a integração real, Jefferson deve fornecer credenciais de
teste por canal seguro e configurar o webhook HTTPS. Fazer compra de teste
pela compra direta e pelo carrinho, conferir preço e referência, retorno,
consulta, pendência, recusa, cancelamento e reembolso. Reenviar notificações e
verificar estoque. Não usar credenciais reais na suíte automatizada.

Antes da produção: validar a aplicação e acesso à Orders API da conta da JBS,
configurar domínio HTTPS e secrets no ambiente, revisar logs e alertas, testar
estados reais, acompanhar criações inconclusivas, ativar a conferência de
pedidos vencidos e definir o frete na etapa final. A devolução de produtos
entregues exige recebimento e conferência antes da solicitação do reembolso. Nenhum deploy é realizado por esta preparação.

Referências oficiais:

- [Criar ordem de Checkout Pro](https://www.mercadopago.com.br/developers/pt/docs/checkout-pro-orders/create-order)
- [Notificações de Orders](https://www.mercadopago.com.br/developers/pt/docs/checkout-pro-orders/notifications)
- [Estados e detalhes](https://www.mercadopago.com.br/developers/pt/docs/checkout-pro-orders/payment-management/status/order-status)
- [Validador de assinatura oficial](https://github.com/mercadopago/sdk-python/blob/master/mercadopago/webhook/validator.py)

## Prazo de 24 horas e conferência de pedidos

Novas ordens de Checkout Pro recebem `expiration_time=P1D`, conforme a
[validade oficial de Orders](https://www.mercadopago.com.br/developers/pt/docs/checkout-pro-orders/additional-settings/define-order-validity).
O prazo do provedor conta a partir da criação remota. Na loja, tentativas sem
pedido expiram após 24 horas; reenvios de pedidos com mais de 24 horas mostram
o estado local e não reabrem o link de pagamento. Ordens já criadas antes dessa
configuração não recebem retroativamente uma nova validade remota.

Para conferir pedidos locais pendentes com pelo menos 24 horas:

```bash
python manage.py expire_pending_orders
# No Docker:
docker compose exec web python manage.py expire_pending_orders
```

A rotina consulta o Mercado Pago e aplica a resposta validada. Se o pagamento
estiver aprovado, preserva o pedido e o estoque. Se estiver em processamento,
preserva a reserva. Para ordens ainda `created` ou `action_required`, solicita
cancelamento no endpoint oficial, com chave idempotente própria, e consulta
novamente antes de liberar estoque. Um conflito HTTP 409 também exige nova
consulta, pois o pagamento pode ter sido aprovado entre as chamadas.

Falha de consulta/cancelamento, valor divergente ou criação sem ID remoto não
libera estoque pelo simples tempo decorrido. Esses casos requerem nova consulta
ou conciliação manual. Confirmação de cancelamento devolve a reserva uma vez.
A conferência continua processando os demais pedidos e retorna erro ao comando
se houver casos sem conciliação, permitindo monitorar a execução.

Preparar o agendador do ambiente para executar esse comando a cada 15 minutos,
sem sobreposição, com as mesmas configurações do serviço web. A validade remota
limita a compra; a conferência periódica pode liberar reservas alguns minutos
depois. Nenhum agendamento foi ativado neste trabalho, nem chamadas reais de
cancelamento foram realizadas. Falhas ou pagamentos em análise podem prolongar
a reserva além de um dia para evitar vender o mesmo estoque duas vezes.

## Reenvio do formulário

O token não contém preço e não substitui CSRF. Token inexistente, inválido,
de outra sessão ou de outra URL não inicia pagamento. Se o carrinho mudar entre
a abertura e o envio, é necessário abrir o checkout novamente. Preço e estoque
são sempre lidos do banco na criação do pedido, mesmo que a página seja antiga.

A criação local e o vínculo com a tentativa são gravados na mesma transação;
a chamada externa ocorre depois, sem manter o banco bloqueado durante a rede.
Uma segunda requisição durante a chamada externa leva ao pedido em confirmação.
Um erro explícito cancela o pedido e emite uma nova tentativa no formulário;
o token antigo continua apontando ao pedido cancelado. O botão de envio é
desativado enquanto a requisição está em andamento e restaurado ao voltar à
página. A proteção de duplicação funciona também sem JavaScript.

O histórico de tentativas deve ser preservado enquanto puder haver reenvios ou
conciliação. A limpeza desses registros não faz parte da rotina de expiração.
Se o processo cair depois de criar o pedido e antes de concluir a chamada remota,
a tentativa permanece ligada ao pedido e requer conciliação; não criaremos um
segundo pedido para resolver uma resposta desconhecida.
