# Regras para futuras alterações

## Git e GitHub

- Ao concluir uma tarefa solicitada, criar um commit após revisar o diff e executar as verificações adequadas à alteração, salvo se o usuário pedir para não fazer commit.
- Incluir no commit somente arquivos relacionados à tarefa. Não incluir segredos, arquivos `.env`, dados locais, uploads ou artefatos gerados.
- Fazer push somente quando o usuário solicitar o envio ao GitHub. A publicação inicial no repositório `joaogabrielcode/store-jbs` foi autorizada.
- Não fazer force push, reescrever histórico nem publicar a aplicação sem autorização explícita.

## Stack e arquitetura

- Stack oficial: Python, Django, Django Templates, Django REST Framework, PostgreSQL, Docker e Docker Compose.
- O projeto é um monólito Django modular; não introduzir microservices, Kubernetes, GraphQL, Redis, Celery ou Kafka sem solicitação explícita.
- O frontend principal deve continuar sendo renderizado com Django Templates.
- APIs futuras devem ser versionadas sob `/api/v1/`.
- Apps: `core` (compartilhado), `products` (catálogo), `orders` (pedidos), `accounts` (usuários/clientes) e `payments` (pagamentos futuros).

## Skills

O conjunto de skills disponível no escopo deste projeto está em `.agents/skills/`.
Não instalar outra skill equivalente sem revisar a sobreposição e atualizar esta
lista. A skill global/local `Django Framework` também orienta a implementação
Django.

Skills presentes no projeto:

- humanize-writing: revisão de textos para português natural, direto e específico.
- ui-anti-slop-codex: critérios para reduzir padrões visuais genéricos e decisões de interface sem função.

- `django-expert`: arquitetura Django, ORM, views, DRF e revisão de backend.
- `django-safe-migration`: migrations Django seguras para PostgreSQL e deploys graduais.
- `django-security`: CSRF, autenticação, autorização, validação e configuração segura.
- `django-tdd`: TDD e testes de Django/DRF.
- `python-patterns`: padrões Python e legibilidade.
- `python-testing`: pytest, fixtures, mocks e parametrização.
- `postgres-patterns`: modelagem, índices, consultas e segurança PostgreSQL.
- `database-migrations`: princípios gerais de migrations e zero downtime.
- `api-design`: recursos REST, status HTTP, versionamento e paginação.
- `docker-patterns`: Dockerfile, Compose, volumes e segurança de containers.
- `grill-me`: entrevista para revisar planos e decisões, acionada explicitamente.
- `grilling`: conduz as rodadas de perguntas usadas por `grill-me`.

As skills `grill-me` e `grilling` foram instaladas de
`mattpocock/skills`, nos caminhos `skills/productivity/grill-me` e
`skills/productivity/grilling`, no commit
`4588b32ecab9ecc9fc8cc6b6c5e7d675b6004b0d`. A segunda é uma dependência da
primeira. Elas complementam as skills técnicas existentes, sem substituí-las.

Os arquivos locais dessas skills não registram de forma uniforme o repositório
GitHub de origem. A seleção foi baseada no conjunto auditado e nos arquivos
presentes no projeto; a proveniência exata deve ser verificada antes de uma
futura reinstalação automática. Não declarar uma origem GitHub como confirmada
sem essa verificação.

Skills não instaladas nesta fase:

- `full-stack-skills/python-skills/django`: descartada por redundância com `django-expert`.
- `django-celery-expert`: reservada para uma fase futura; não introduzir Celery, Redis ou processamento assíncrono agora.
- `django-patterns`: não existe no conjunto local; não duplicar `django-expert`.

Ao usar as skills, combinar apenas as instruções relevantes à tarefa. Em caso
de conflito, priorizar este arquivo, as instruções do usuário e a documentação
oficial do Django/DRF.

- Trabalhar somente no escopo solicitado.
- Não implementar fases futuras automaticamente.
- Não adicionar dependências sem necessidade.
- Manter regras de negócio no backend.
- Nunca confiar em preço ou total enviados pelo navegador.
- Nunca colocar segredos no código.
- Criar migrations quando models forem alterados.
- Evitar duplicação.
- Manter templates reutilizáveis.
- Criar componentes ou parciais para elementos repetidos.
- Manter código Python organizado e legível.
- Escrever testes para regras críticas.
- Atualizar a documentação quando a arquitetura mudar.

Todas as novas páginas devem reutilizar o mesmo container, grid, escala de
espaçamento, tipografia e componentes definidos em docs/layout-guidelines.md.
Consultar também docs/design-system.md para composição e regras de conteúdo.
Evitar layouts full-width ou elementos esticados sem motivo funcional.

## Anti-AI / Anti-Slop Guidelines

As skills humanize-writing e ui-anti-slop-codex estão instaladas no ambiente
Codex e fazem parte das regras deste projeto. Aplicá-las em toda nova alteração
de texto, microcopy, componente e decisão visual do storefront.

- Escrever em português brasileiro natural, curto e específico para a JBS Solar.
- Remover travessões longos usados como vício estilístico e evitar títulos, slogans
  e descrições que apenas ocupem espaço.
- Não usar em dash/travessão longo (—) como recurso estilístico na copy da JBS
  Store, inclusive nos nomes acessíveis. Não usar sequências decorativas de
  hífens ou underscores para separar conteúdo visível.
- Evitar fórmulas como “Mais do que X, Y”, “Não é apenas X, é Y”, “Descubra uma
  nova forma de...” e “Transforme sua experiência...”.
- Não inventar números, avaliações, benefícios, depoimentos, selos ou métricas.
  Usar somente informações presentes no produto, no pedido ou na regra de negócio.
- Evitar buzzwords e repetição de termos vagos como solução, experiência, jornada,
  ecossistema, robusto, moderno e completo quando não acrescentarem informação.
- Antes de adicionar copy, confirmar que ela comunica algo real. Caso contrário,
  remover ou simplificar.
- Priorizar hierarquia, legibilidade, contraste, espaçamento consistente e
  componentes úteis para e-commerce de energia solar.
- Evitar excesso de cards, card dentro de card, grids de preenchimento, gradientes
  decorativos, glow, blobs, glassmorphism, sombras fortes, bordas exageradas,
  badges sem função, métricas fictícias e animações decorativas.
- Antes de criar um componente visual, verificar se ele parece específico da JBS
  Solar. Se poderia pertencer a qualquer template, simplificar ou adaptá-lo.
- Manter as funcionalidades existentes e preferir ajustes pequenos e verificáveis
  a uma reformulação visual ampla.
- Manter o CSS do storefront e do Django Admin isolados. Nunca carregar estilos
  da loja em `/admin/` nem estilos do admin na loja.
- Evitar seletores globais no storefront e no admin; novos componentes devem ser
  escopados ao contexto em que são usados (`.store-app` ou `.admin-interface`).
