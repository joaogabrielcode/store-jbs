# JBS Store — Design System & UI Specification

> Documento de referência visual para implementação da loja da JBS Solar com Django Templates.
>
> Baseado nos quatro layouts de referência fornecidos:
> 1. Home da loja
> 2. Catálogo / listagem de produtos
> 3. Página de produto
> 4. Checkout
>
> Este arquivo deve ser tratado pelo Codex como **fonte de verdade visual** para o frontend da loja.

---

# 1. Objetivo visual

A JBS Store deve transmitir:

- confiança;
- tecnologia;
- energia;
- profissionalismo;
- clareza;
- organização;
- sensação de produto premium;
- forte identidade solar/energética;
- experiência de e-commerce limpa e objetiva.

O design deve preservar a identidade da landing page da JBS Solar, mas adaptada para uma experiência de loja.

A interface deve combinar:

- grandes áreas claras para catálogo e leitura;
- azul-marinho para header, hero, banners e footer;
- laranja como cor principal de conversão;
- azul/ciano como destaque secundário;
- cards brancos com bordas e sombras leves;
- tipografia moderna, sem excesso de peso visual.

Evitar:

- gradientes excessivos;
- sombras pesadas;
- muitos tons diferentes de azul;
- cantos exageradamente arredondados;
- elementos com estética genérica de marketplace;
- excesso de animações;
- excesso de informação em uma mesma área.

---

# 2. Princípios de interface

## 2.1 Hierarquia

A hierarquia deve ser sempre clara:

1. Título principal
2. Subtítulo / texto de apoio
3. CTA principal
4. CTA secundário
5. Informação complementar
6. Elementos decorativos

## 2.2 Consistência

Todos os componentes repetidos devem usar os mesmos:

- espaçamentos;
- radius;
- sombras;
- tamanhos de ícone;
- estilo de botão;
- estados de hover;
- tipografia;
- tokens de cor.

## 2.3 Conversão

Ações principais devem usar laranja.

Exemplos:

- Adicionar ao carrinho
- Ver produtos
- Finalizar pedido
- Quero receber
- Conhecer curso

Ações secundárias devem usar:

- azul;
- outline;
- link com seta;
- botão ghost.

## 2.4 Densidade visual

A loja deve parecer organizada e respirada.

Evitar:

- texto encostado em borda;
- cards apertados;
- grids sem gap;
- muitos elementos em uma mesma linha.

---

# 3. Design Tokens

## 3.1 Cores

Usar estes tokens como base.

```css
:root {
  /* Brand / Navy */
  --color-navy-950: #081A2C;
  --color-navy-900: #0A2744;
  --color-navy-850: #0E3153;
  --color-navy-800: #123A60;

  /* Blues */
  --color-blue-700: #1C5F98;
  --color-blue-600: #1F79C6;
  --color-blue-500: #2F95E8;
  --color-cyan: #36BCEB;

  /* Accent */
  --color-orange: #FF671F;
  --color-orange-hover: #E95A12;
  --color-orange-soft: #FFF0E8;

  /* Neutral */
  --color-white: #FFFFFF;
  --color-bg: #F7F9FB;
  --color-bg-soft: #F0F5F8;
  --color-surface: #FFFFFF;
  --color-surface-muted: #F5F8FA;

  /* Text */
  --color-text: #0B2A4B;
  --color-text-secondary: #617286;
  --color-text-muted: #8797A8;
  --color-text-inverse: #FFFFFF;

  /* Border */
  --color-border: #D9E3EC;
  --color-border-strong: #C7D4E0;

  /* Status */
  --color-success: #1FA463;
  --color-success-soft: #EAF8F0;
  --color-warning: #F5A000;
  --color-danger: #D94F4F;
}
```

### Regras de uso

- Laranja: CTAs, badges promocionais e pequenos destaques.
- Ciano: palavras-chave, ícones ou detalhes.
- Navy: grandes áreas institucionais, hero, header e footer.
- Branco: cards, formulários, catálogo e áreas de leitura.
- Azul: links, ícones e estados interativos.
- Verde: estoque, sucesso e WhatsApp.
- Cinza-azulado: texto secundário e bordas.

Não criar novos tons sem necessidade.

---

# 4. Tipografia

## 4.1 Fontes

```text
Headings: Manrope
Body/UI: Inter
```

Fallbacks:

```css
font-family: "Manrope", "Inter", system-ui, sans-serif;
```

## 4.2 Escala tipográfica

```text
Display / Hero:
56–64px desktop
42–48px tablet
34–40px mobile
weight 700
line-height 1.0–1.08

H1:
48–56px
weight 700

H2:
34–42px
weight 700

H3:
24–30px
weight 600–700

H4:
18–22px
weight 600

Body:
16px
weight 400
line-height 1.5–1.65

Body small:
14px

Caption / eyebrow:
12px
weight 600
uppercase opcional
letter-spacing: .04em
```

## 4.3 Destaques

Palavras em títulos podem usar:

- ciano;
- laranja;
- branco em fundo escuro.

Nunca usar várias cores no mesmo título sem necessidade.

---

# 5. Espaçamento

Criar escala consistente:

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
--space-20: 80px;
--space-24: 96px;
```

## Regras

- Seção grande: 72–96px vertical
- Card: 20–28px padding
- Grid gap: 20–24px
- Form gap: 16–20px
- Hero conteúdo: 24–32px entre blocos
- Header: 16–24px horizontal

---

# 6. Container e Grid

## 6.1 Container

```css
--container-max: 1320px;
--container-padding: 24px;
```

Mobile:

```text
padding horizontal: 16px
```

Wide:

```text
max-width entre 1280 e 1360px
```

## 6.2 Grid

Desktop:

- 12 colunas
- gap 20–24px

Catálogo:

```text
Sidebar: 240–280px
Conteúdo: restante
```

Grid de produtos:

```text
4 colunas desktop
3 colunas desktop menor
2 colunas tablet
1–2 colunas mobile
```

---

# 7. Bordas e Radius

```css
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 16px;
--radius-xl: 20px;
--radius-pill: 999px;
```

Uso:

- Inputs: 8px
- Botões: 8–10px
- Cards de produto: 12–16px
- Cards de categoria: 12–16px
- Banners: 16–20px
- Badges: pill

---

# 8. Sombras

Sombras leves.

```css
--shadow-sm: 0 4px 16px rgba(8, 26, 44, 0.06);
--shadow-md: 0 8px 28px rgba(8, 26, 44, 0.09);
--shadow-hover: 0 12px 34px rgba(8, 26, 44, 0.12);
```

Nunca usar sombra preta pesada.

---

# 9. Ícones

Usar uma única biblioteca.

Preferência:

```text
Lucide Icons
```

Características:

- outline;
- stroke consistente;
- azul/ciano/navy;
- 18–28px;
- círculos ou fundos suaves apenas quando fizer sentido.

Não misturar:

- emoji;
- Font Awesome;
- ícones aleatórios;
- SVGs inconsistentes.

---

# 10. Botões

## 10.1 Primário

```css
.btn-primary {
  background: var(--color-orange);
  color: var(--color-white);
  border: 0;
  border-radius: 10px;
  font-weight: 600;
  min-height: 46px;
  padding: 0 20px;
}
```

Hover:

```css
background: var(--color-orange-hover);
transform: translateY(-1px);
```

## 10.2 Secundário

Em fundo escuro:

```css
background: transparent;
border: 1px solid rgba(255,255,255,.6);
color: white;
```

Em fundo claro:

```css
background: white;
border: 1px solid var(--color-border);
color: var(--color-text);
```

## 10.3 Link

```text
Ver todos os produtos →
Ver detalhes →
Conheça →
```

Azul ou ciano.

---

# 11. Inputs e Forms

```css
input,
select,
textarea {
  min-height: 48px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-white);
  color: var(--color-text);
}
```

Focus:

```css
border-color: var(--color-blue-500);
box-shadow: 0 0 0 3px rgba(47,149,232,.12);
```

Placeholder:

```text
cinza-azulado suave
```

Labels:

```text
14px
weight 500–600
```

---

# 12. Header

## Estrutura

```text
[Logo]

Início
Serviços
Orçamento
FAQ
Loja JBS

[Busca................]

Instagram
Carrinho
```

## Estilo

- fundo navy;
- altura aproximada: 72–80px;
- conteúdo centralizado no container;
- links brancos;
- item ativo com underline laranja;
- busca integrada;
- carrinho com badge.

## Busca

- fundo branco com leve transparência;
- ícone de lupa;
- borda sutil;
- largura grande em desktop.

## Carrinho

- ícone branco;
- badge laranja;
- contador branco.

## Mobile

- logo;
- busca;
- carrinho;
- botão de menu.

---

# 13. Eyebrow de seção

Padrão visual:

```text
— CATEGORIAS
```

Com:

- linha laranja pequena;
- label azul/ciano;
- uppercase;
- 12px;
- weight 600.

Exemplos:

```text
— CATEGORIAS
— DESTAQUES
— CURSO EM DESTAQUE
— POR QUE COMPRAR NA LOJA JBS?
— DEPOIMENTOS
— SUPORTE ESPECIALIZADO
```

---

# 14. Hero da Home

## Estrutura

```text
Header

Hero com imagem solar

Eyebrow: LOJA JBS

Tudo para o seu
projeto solar, em um
só lugar.

Texto de apoio

[Ver todos os produtos]
[Conheça nossos cursos]

                    card visual / mensagem

Faixa de benefícios
```

## Regras

- imagem solar full-width;
- overlay navy;
- texto branco;
- destaque em ciano;
- CTA laranja;
- CTA secundário outline;
- máximo 2 CTAs;
- card lateral translúcido opcional;
- hero 500–600px desktop.

## Benefícios no rodapé do hero

4 itens:

- entrega;
- compra segura;
- qualidade;
- suporte.

Ícone + título + descrição.

---

# 15. Seção de Categorias

## Estrutura

```text
Eyebrow
Título
Texto auxiliar
Link "Ver todas as categorias"

[card][card][card][card][card]
```

## CategoryCard

Conteúdo:

- ícone;
- título;
- descrição curta;
- imagem;
- link.

Estilo:

- fundo branco;
- borda;
- radius 12–16px;
- padding 20–24px;
- hover suave.

---

# 16. ProductCard

Componente essencial e reutilizável.

## Estrutura

```text
[badge]                    [favorito]

          imagem

Nome do produto
Descrição curta

★★★★★ (124)

Preço anterior opcional
R$ 1.249,90
parcelamento

[Adicionar ao carrinho]
```

## Regras

- imagem grande;
- fundo branco;
- borda;
- radius 12–16px;
- preço em navy forte;
- CTA laranja full-width;
- badge no topo;
- favorito no canto;
- descrição curta limitada a poucas linhas.

## Badges

```text
Mais vendido
Promoção
Kit completo
Curso online
Lançamento
Energia por assinatura
```

Laranja para promoções.
Azul/ciano para categorias/status.

## Hover

```text
translateY(-3px)
shadow suave
border azul suave
```

---

# 17. Banner de Curso

## Estrutura

```text
CURSO EM DESTAQUE

Formação Completa
em Energia Solar

Texto

[Quero conhecer o curso]

                 lista de benefícios
                 notebook / imagem
```

## Visual

- fundo navy;
- título branco;
- palavra ciano;
- botão laranja;
- imagem grande na direita;
- ícones simples.

---

# 18. Benefícios da Loja

## Título

```text
Mais que produtos, uma parceria
para o seu projeto.
```

## Cards

4 cards horizontais:

- Compra 100% segura
- Entrega em todo o Brasil
- Suporte especializado
- Pagamento facilitado

Card:

- ícone azul;
- título navy;
- descrição muted;
- branco;
- borda fina.

---

# 19. Depoimentos

## Estrutura

```text
Quem já comprou
recomenda.

[card][card][card]
```

Cada card:

- avatar;
- nome;
- tipo de cliente;
- estrelas;
- texto.

Estilo clean.

---

# 20. Newsletter

## Estrutura

```text
imagem / textura solar

Ofertas exclusivas,
lançamentos e conteúdos
sobre energia solar.

[email.......................][Quero receber]
```

## Visual

- navy;
- imagem no fundo ou lateral;
- texto branco;
- CTA laranja;
- form horizontal desktop;
- vertical mobile.

---

# 21. Footer

## Estrutura

```text
Logo + slogan

Institucional
Ajuda
Atendimento
Formas de pagamento
```

Rodapé:

```text
© JBS Solar
Energia limpa hoje. Mais possibilidades para amanhã.
```

## Visual

- navy muito escuro;
- títulos brancos;
- links em cinza-claro;
- hover ciano;
- ícones sociais;
- formas de pagamento organizadas.

---

# 22. Página de Catálogo

## Hero interno

Banner menor que o hero da home.

Conteúdo:

```text
Produtos da Loja JBS

Cursos, materiais, kits e soluções completas
para o seu projeto solar, em um só lugar.
```

Com imagem solar e overlay navy.

Faixa de benefícios logo abaixo.

## Layout

```text
[Sidebar]     [Conteúdo]

Categorias   quantidade
Preço        ordenação
Marcas       grid de produtos
Disponib.    paginação
```

## Sidebar

Cards separados para:

- Categorias
- Faixa de preço
- Marcas
- Disponibilidade

Estilo:

- branco;
- borda;
- radius 12px;
- padding 16–20px.

## Categoria ativa

- fundo azul claro;
- texto azul;
- borda ou barra lateral azul.

## Mobile

Sidebar vira:

- drawer;
- modal;
- botão "Filtrar".

---

# 23. Página de Produto

## Hero interno

Pode usar banner solar compacto com:

```text
Energia solar
para a sua realidade.
```

## Conteúdo principal

Duas colunas:

### Esquerda

- galeria;
- imagem principal;
- thumbnails;
- badge.

### Direita

- categoria;
- badge;
- título;
- rating;
- descrição;
- benefícios em linha;
- preço;
- parcelamento;
- estoque;
- quantidade;
- adicionar ao carrinho;
- WhatsApp;
- selos de confiança.

## Quantidade

```text
[-] 1 [+]
```

## CTA principal

Laranja e largo.

## WhatsApp

Outline verde.

---

# 24. Benefícios do Produto

Seção:

```text
Por que escolher este kit?
```

4 cards:

- economia;
- energia limpa;
- kit completo;
- marcas líderes.

---

# 25. Tabs do Produto

Tabs:

```text
Descrição
O que está incluso
Especificações
Instalação
Envio
```

Ativo:

- laranja;
- underline;
- texto destacado.

Conteúdo:

- texto à esquerda;
- resumo / lista à direita.

Mobile:

- accordion é aceitável.

---

# 26. Produtos Complementares

Grid de cards menores.

Mesmo ProductCard, porém compacto.

---

# 27. CTA Técnico

Antes do footer:

```text
SUPORTE ESPECIALIZADO

Conte com a orientação
técnica da JBS Solar.

Texto

[Falar com um especialista]

              benefícios
              imagem / pessoa / produto
```

Visual navy.

---

# 28. Checkout

## Hero

```text
Finalize sua compra

É rápido, seguro e você está a poucos passos
de receber seus produtos da JBS Solar.
```

Navy com imagem solar.

## Stepper

```text
1 Carrinho
2 Identificação
3 Pagamento
4 Confirmação
```

Ativo em laranja.

## Layout

Desktop:

```text
Esquerda: 65%
Direita: 35%
```

### Esquerda

Cards:

- Seus dados
- Endereço
- Forma de pagamento

### Direita

- Resumo do pedido
- Benefícios
- Ajuda

## Resumo

Itens com:

- thumbnail;
- nome;
- quantidade;
- preço.

Depois:

- subtotal;
- frete;
- total;
- parcelamento;
- CTA.

Resumo pode ficar sticky em desktop.

---

# 29. Checkout — Formulários

## Seus dados

Campos:

- Nome completo
- E-mail
- WhatsApp
- CPF

## Endereço

Campos:

- CEP
- Endereço
- Número
- Complemento
- Bairro
- Cidade
- Estado
- Observação

## Pagamento

Abas:

- Cartão
- PIX
- Boleto
- Mercado Pago

Visual com tabs/cards.

Não implementar lógica fictícia de pagamento.
O layout deve estar preparado para integração real.

---

# 30. Estados

## Loading

Usar skeletons suaves.

## Empty state

Exemplo:

```text
Nenhum produto encontrado.
Tente ajustar os filtros.
```

## Error

Card simples com mensagem e ação.

## Estoque

```text
Em estoque → verde
Poucas unidades → amarelo
Indisponível → vermelho/cinza
```

---

# 31. Animações

Usar movimento discreto.

## Entrada

```text
opacity 0 → 1
translateY 16px → 0
duration 400–600ms
```

## Hover de card

```text
translateY(-3px)
shadow suave
```

## Botão

```text
translateY(-1px)
```

## Regras

- sem animações exageradas;
- usar `transform` e `opacity`;
- respeitar `prefers-reduced-motion`.

---

# 32. Responsividade

## Breakpoints

```text
mobile: < 640px
tablet: 640–1024px
desktop: > 1024px
wide: > 1280px
```

## Mobile

- hero empilha;
- CTA full-width quando necessário;
- categorias 1 coluna;
- produtos 1–2 colunas;
- sidebar vira drawer;
- checkout 1 coluna;
- resumo vai abaixo;
- footer empilha;
- busca pode ocupar linha separada;
- tabs podem virar accordion.

---

# 33. Arquitetura Django Templates

Estrutura recomendada:

```text
templates/
├── base.html
├── components/
│   ├── header.html
│   ├── footer.html
│   ├── product_card.html
│   ├── category_card.html
│   ├── benefit_card.html
│   ├── testimonial_card.html
│   ├── breadcrumb.html
│   ├── newsletter.html
│   ├── section_heading.html
│   └── pagination.html
├── store/
│   ├── home.html
│   ├── catalog.html
│   └── product_detail.html
├── cart/
│   └── cart.html
└── checkout/
    └── checkout.html
```

Nunca duplicar grandes blocos de markup.

---

# 34. CSS

Estrutura sugerida:

```text
static/css/
├── tokens.css
├── base.css
├── layout.css
├── components.css
├── utilities.css
└── pages/
    ├── store-home.css
    ├── catalog.css
    ├── product-detail.css
    └── checkout.css
```

Ou equivalente usando uma arquitetura CSS simples.

## Regras

- tokens em um arquivo central;
- evitar valores hardcoded repetidos;
- evitar `!important`;
- evitar CSS inline;
- componentes reutilizáveis;
- mobile-first.

---

# 35. JavaScript

Usar JavaScript apenas quando necessário.

Exemplos:

- menu mobile;
- carrinho;
- quantidade;
- galeria;
- tabs;
- filtros;
- drawer mobile;
- newsletter;
- interações simples.

Evitar framework frontend nesta fase.

---

# 36. Acessibilidade

Obrigatório:

- contraste suficiente;
- labels de formulário;
- foco visível;
- botões reais;
- links semânticos;
- alt em imagens;
- navegação por teclado;
- aria quando necessário;
- estado de erro acessível.

---

# 37. Conteúdo Fictício

As referências apresentam:

- produtos;
- preços;
- avaliações;
- parcelamentos;
- promoções;
- depoimentos;
- frete;
- marcas;
- garantias.

Esses dados servem apenas como referência de layout.

O Codex NÃO deve assumir esses valores como reais.

Não inventar:

- preço;
- marca;
- prazo;
- garantia;
- avaliação;
- desconto;
- frete;
- forma de pagamento;
- disponibilidade;
- condição comercial.

Usar dados mockados claramente identificados enquanto não houver dados reais.

---

# 38. Ordem de Implementação

## Fase 1 — Fundação visual

Criar:

- tokens;
- base;
- container;
- grid;
- typography;
- buttons;
- inputs;
- cards;
- header;
- footer.

## Fase 2 — Home

Criar:

- hero;
- benefícios;
- categorias;
- destaques;
- banner de curso;
- benefícios da loja;
- depoimentos;
- newsletter.

## Fase 3 — Catálogo

Criar:

- hero interno;
- sidebar;
- filtros;
- ordenação;
- grid;
- paginação.

## Fase 4 — Produto

Criar:

- galeria;
- dados;
- preço;
- quantidade;
- CTAs;
- benefícios;
- tabs;
- complementares;
- CTA técnico.

## Fase 5 — Carrinho

Criar:

- lista de itens;
- quantidade;
- remoção;
- resumo.

## Fase 6 — Checkout

Criar:

- stepper;
- dados;
- endereço;
- pagamento;
- resumo;
- confirmação.

---

# 39. Regras para o Codex

Ao implementar qualquer página:

1. Ler este arquivo antes.
2. Reutilizar os tokens.
3. Reutilizar componentes existentes.
4. Não criar nova paleta.
5. Não duplicar componentes.
6. Não adicionar dependência sem necessidade.
7. Não alterar backend sem solicitação.
8. Não implementar funcionalidades futuras automaticamente.
9. Não inventar conteúdo comercial.
10. Validar responsividade.
11. Validar acessibilidade básica.
12. Rodar testes e checks relevantes.
13. Preservar identidade visual da JBS.
14. Não usar React, Next ou Vue.
15. Usar Django Templates para o frontend.

---

# 40. Prompt-base para futuras tarefas

Use este padrão ao trabalhar com Codex:

```text
Leia primeiro:
- docs/design-system.md
- AGENTS.md

Tarefa:
[descrever uma única feature]

Escopo:
[arquivos/componentes que podem ser alterados]

Não alterar:
[áreas fora do escopo]

Requisitos visuais:
seguir integralmente docs/design-system.md

Requisitos técnicos:
- Django Templates
- reutilizar componentes
- mobile-first
- acessibilidade básica
- sem nova dependência sem necessidade

Validação:
- verificar responsividade
- executar checks relevantes
- informar arquivos alterados

Não avance para outra feature.
```

---

# 41. Resultado esperado

A loja deve ter aparência consistente em todas as páginas.

A sensação visual deve ser:

```text
JBS Solar
+
e-commerce profissional
+
energia / tecnologia
+
alto nível de confiança
+
interface limpa
+
boa conversão
```

A Home, Catálogo, Produto e Checkout devem parecer partes do mesmo sistema, e não páginas criadas separadamente.

---

# 42. Referência visual

As quatro imagens fornecidas devem ser usadas como referência de composição:

```text
Home da loja
Catálogo
Página de produto
Checkout
```

O objetivo é reproduzir:

- hierarquia;
- ritmo;
- proporções;
- estilo de cards;
- paleta;
- organização;
- densidade visual;
- relacionamento entre seções.

Não é necessário reproduzir literalmente textos, preços ou produtos fictícios.
