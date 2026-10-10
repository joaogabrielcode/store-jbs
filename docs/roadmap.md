# Roadmap da JBS Solar Store

Este roadmap define a ordem recomendada de evolução da loja. Cada fase deve ser
implementada e validada antes de avançar para a próxima. Não implementar fases
futuras automaticamente.

## Fases

### 1. Fundação do projeto — concluída

- Estrutura do monólito Django.
- Apps `core`, `products`, `orders`, `accounts` e `payments`.
- Django Templates, DRF, PostgreSQL e Docker Compose configurados.
- Documentação, testes iniciais e skills do projeto configurados.

### 2. Catálogo e produtos — próxima fase

- Criar os models `Category` e `Product` em `products`.
- Definir campos mínimos: nome, slug, descrição, preço com `DecimalField`,
  estoque, status ativo, categoria e imagem principal.
- Adicionar constraints, índices somente quando necessários e migrations.
- Configurar o Django Admin.
- Escrever testes dos models e das regras básicas.

**Entrega:** produtos cadastráveis pelo Admin.

### 3. Catálogo público

- Criar listagem de produtos.
- Adicionar filtro por categoria, busca simples, ordenação e paginação.
- Criar página individual do produto.
- Reutilizar templates para cards, mensagens e estados vazios.

**Entrega:** visitantes conseguem navegar e consultar produtos.

### 4. Carrinho

- Implementar carrinho baseado em sessão.
- Adicionar, alterar quantidade e remover produtos.
- Validar estoque no backend.
- Recalcular preços e totais no servidor.
- Testar quantidades, estoque e cálculos.

**Entrega:** cliente consegue montar um pedido temporário.

### 5. Autenticação e contas

- Decidir o modelo de usuário antes de criar dependências com pedidos.
- Implementar cadastro, login, logout e recuperação de senha.
- Criar perfil e endereços somente quando forem necessários.
- Testar autenticação, autorização e acesso a dados privados.

### 6. Pedidos

- Criar `Order` e `OrderItem` em `orders`.
- Armazenar snapshots do nome e preço dos produtos no pedido.
- Modelar endereço de entrega e status do pedido.
- Criar pedidos usando transações atômicas.
- Validar estoque no backend.
- Nunca confiar no total enviado pelo navegador.

**Entrega:** carrinho pode ser convertido em pedido persistido.

### 7. Checkout sem pagamento

- Criar tela de revisão dos itens.
- Receber dados do cliente e endereço.
- Calcular subtotal, frete e total no backend.
- Criar pedido com status inicial, como `pending_payment`.
- Exibir confirmação do pedido.

### 8. Mercado Pago

Implementar somente depois de o fluxo de pedidos estar estável:

- Isolar a integração em `payments`.
- Manter tokens exclusivamente no `.env`.
- Criar pagamentos no backend.
- Implementar webhook.
- Validar o webhook e consultar o pagamento no Mercado Pago.
- Atualizar o pedido somente após confirmação confiável.
- Testar respostas da integração com mocks.

### 9. Área do cliente

- Exibir histórico de pedidos.
- Exibir detalhes e status de cada pedido.
- Permitir gerenciamento de dados e endereços quando necessário.

### 10. API DRF

Criar somente endpoints com necessidade real, versionados sob `/api/v1/`:

- produtos;
- categorias;
- pedidos.

Cada endpoint deve ter serializers, paginação, autenticação e permissions
adequados. O site principal continua sendo renderizado com Django Templates.

### 11. Testes e qualidade

- Ampliar testes de models, services, views, serializers e permissions.
- Cobrir carrinho, pedidos, estoque, checkout e pagamentos.
- Executar `pytest`, `python manage.py check` e verificações de migrations.
- Adicionar testes de integração para os fluxos críticos.

### 12. Preparação para produção e deploy

- Revisar `DEBUG`, `ALLOWED_HOSTS`, CSRF e cookies seguros.
- Configurar HTTPS, arquivos estáticos e media.
- Adicionar health check e logging.
- Definir backup e restauração do PostgreSQL.
- Validar migrations em staging antes da produção.
- Documentar o processo de deploy.

## Ordem do próximo ciclo

1. Models `Category` e `Product`.
2. Migrations e Django Admin.
3. Testes dos models.
4. Listagem e detalhe do produto.
5. Carrinho em sessão.

## Fora do escopo inicial

Não adicionar sem solicitação explícita:

- Redis;
- Celery;
- Kafka;
- GraphQL;
- Kubernetes;
- microservices;
- otimizações ou abstrações prematuras;
- APIs sem necessidade real.
