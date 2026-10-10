# Padrão atual da JBS Store

Este guia registra as regras atuais da loja. Use-o junto com `AGENTS.md` e
`docs/layout-guidelines.md`. O arquivo `docs/jbs-store-design-system.md` contém a
referência visual inicial; em divergências de dimensões e composição, prevalecem
este guia, as regras de layout atuais e as instruções da tarefa.

## Consistência das páginas internas

Todas as futuras páginas internas devem reutilizar o mesmo padrão de container,
tipografia, espaçamento, grid, botões, cards e linguagem visual do storefront.

- Container `.shell`: máximo de 1200 px e gutters de 24 px em cada lado.
- Tipografia: Manrope para títulos e Inter para textos e controles.
- Espaçamento e grids: seguir `docs/layout-guidelines.md` e os componentes atuais.
- Botões: reutilizar `.button` e suas variantes; área de toque de pelo menos 44 px.
- Cards: reutilizar `templates/components/product_card.html` quando aplicável,
  com bordas discretas e imagens de proporção consistente.
- Cores: tokens existentes de azul-marinho, ciano, laranja e branco em
  `static/css/main.css`. Não adicionar paleta, framework ou biblioteca para
  reproduzir componentes existentes.
- CSS: escopar a `.store-app`, mantendo o Admin separado.
- Estados: preservar foco visível, seleção, busca sem resultados e responsividade.

## Hero compacta do catálogo

- Manter a imagem `static/images/painel-solar-image.png` como fundo e ajustar
  posição e overlay apenas para garantir legibilidade.
- Cabeçalho no fluxo da página do catálogo, sem sobrepor a composição da hero.
- Altura mínima de 320 px no desktop, sem contar o cabeçalho.
- Conteúdo alinhado ao container do catálogo e centralizado verticalmente na área
  acima dos benefícios.
- Título: 52 px no desktop, 42 px no tablet e 32 px no mobile.
- Identificação e título usam Loja JBS Solar, com o nome em ciano no título.
- A descrição de cursos, materiais, kits e produtos aparece logo abaixo do título.
- Texto de apoio com largura máxima de 550 px.
- Ações próximas ao texto: ver todos os produtos e conhecer kits solares.
- Quatro benefícios com ícones SVG de traço consistente, em uma linha no desktop
  e duas colunas nas telas menores. No mobile, a altura acompanha o conteúdo,
  sem espaço vazio para imitar a versão desktop.
- Preservar os textos fornecidos para a tarefa sem acrescentar alegações,
  métricas, selos ou condições comerciais.

## Guia de conteúdo

Nos produtos físicos, Comprar agora é a ação principal em laranja e Adicionar ao
carrinho é a ação secundária. Nos cards, as ações ocupam duas linhas com área de
toque mínima de 44 px. Nome e imagem levam aos detalhes. Na página do produto,
as duas ações compartilham a quantidade selecionada. No checkout de compra direta,
o resumo informa o item, a quantidade, o total e que o carrinho permanece salvo.

Não usar em dash/travessão longo (—) como recurso estilístico na copy da JBS Store.

A regra se aplica a títulos, descrições, labels, botões, mensagens e nomes
acessíveis. Não usar sequências decorativas de hífens ou underscores para separar
conteúdo visível. Usar espaço, ponto, vírgula, dois-pontos, borda CSS, grid ou
alinhamento conforme a função.

Escrever em português brasileiro natural, curto e específico. Não inventar
benefícios ou dados comerciais e não adicionar textos apenas para ocupar espaço.
