# Layout guidelines

Estas regras mantêm as páginas da Loja JBS Solar alinhadas entre si. Novas
seções devem reutilizar os tokens e componentes existentes antes de criar uma
variação local.

## Container e gutters

- Container padrão: max-width de 1200px.
- Largura: min(100% - 48px, 1200px).
- Centralização: margin-inline: auto.
- O mesmo container deve ser usado no hero, nas seções internas, no banner, no
  rodapé e na navegação.
- Fundos podem ocupar a viewport inteira, mas o conteúdo deve permanecer dentro
  do container.

## Espaçamento

Use a escala existente em main.css e evite valores isolados. Como referência:

- seção: 64px a 72px no desktop;
- seção em telas menores: 56px;
- gap de grid: 12px a 18px;
- padding de card: 16px a 18px;
- distância entre título e apoio: 8px a 16px.

## Grids padrão

- Categorias: 4 colunas no desktop, 2 no tablet e 1 no mobile.
- Produtos em destaque: 3 colunas no desktop, 2 no tablet e 1 no mobile.
- Benefícios: 4 colunas no desktop, 2 no tablet e 1 no mobile.
- Cards devem usar min-width: 0 e não devem crescer apenas para preencher
  espaço disponível.

## Seções e texto

O cabeçalho de seção segue esta ordem:

1. eyebrow;
2. título;
3. texto auxiliar opcional;
4. link opcional.

O título e o texto auxiliar devem permanecer no mesmo grid. Textos corridos
devem ter largura controlada, normalmente entre 320px e 580px, conforme o
contexto.

## Cards e imagens

- Cards da mesma seção usam o mesmo radius, padding e alinhamento.
- Ações de produto ficam no rodapé do card.
- Imagens de produto usam proporção controlada e object-fit: contain.
- Placeholders devem respeitar a mesma área da imagem real.
- Evitar card dentro de card, alturas artificiais e áreas vazias sem função.

## Tipografia e responsividade

- Usar as fontes e os tokens definidos em main.css.
- Manter títulos curtos e contidos no grid.
- Não usar largura de viewport para esticar texto ou componentes.
- Em telas menores, reduzir colunas antes de reduzir legibilidade.
- Todos os elementos devem respeitar o gutter de 24px, inclusive no mobile.
