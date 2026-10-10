# Regras comerciais confirmadas

Produtos físicos mantêm Comprar agora e carrinho, ambos com Mercado Pago.
Cursos usam somente checkout Hotmart.

## Cursos

Usar o preço normal da oferta principal, sem escolher ofertas promocionais
alternativas. O preço e o link são recebidos da Hotmart; a oferta principal
precisa estar configurada corretamente nessa plataforma.

A compra é única. O parcelamento divide o custo do curso e é oferecido pelo
checkout Hotmart conforme sua configuração. Não há assinatura ou mensalidade.
A loja apresenta o preço total, sem inventar valor de parcela ou juros.

Sincronizar às 06h, 14h e 22h, no fuso America/Sao_Paulo. Ativar o agendador
quando o ambiente e as credenciais estiverem prontos.

## Prazo e reserva

O cliente tem 24 horas para concluir a compra do produto físico no Mercado
Pago. Novas ordens remotas usam validade de um dia. A rotina
`expire_pending_orders` confere pedidos locais vencidos e só devolve estoque
após confirmação de cancelamento ou falha definitiva pelo provedor.
Pagamento em análise, erro de rede ou criação inconclusiva exige conciliação;
o simples relógio não autoriza liberar mercadoria que pode ter sido paga.

Reenvios do mesmo formulário, inclusive concorrentes, usam a mesma tentativa,
o mesmo pedido e a mesma reserva. Abrir um novo formulário permite outra compra.

## Devolução de produto físico entregue

Fluxo operacional definido pelo usuário:

1. O cliente combina a devolução com a JBS.
2. A JBS recebe e confere o produto devolvido.
3. Após essa confirmação, o responsável solicita o reembolso no provedor.
4. O webhook registra o reembolso confirmado pelo Mercado Pago.
5. A equipe decide se o produto pode voltar ao estoque após a conferência.

Não há solicitação automática de reembolso no código atual, nem portal de
devoluções ou registro de recebimento físico implementado. A conferência e a
solicitação ao provedor continuam operações manuais. O webhook não deve ocultar
um reembolso já realizado pelo Mercado Pago por falta de confirmação local.

Cancelamento antes do envio e reembolsos de cursos não exigem retorno de uma
mercadoria já entregue. Cursos são atendidos na Hotmart. Esta documentação
registra o fluxo operacional; não publica um termo de devolução ao consumidor.

## Frete

Resolver na etapa final, por decisão do usuário. O cálculo atual permanece em
zero durante a preparação. Isso não confirma frete gratuito para a operação real.
