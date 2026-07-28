# ADR-003: Modelagem de Dados Relacional e Arquitetura Modular do Banco de Dados

**Status:** Aceito  
**Data:** 2026-07-27  
**Decisores:** Otavio (Data Scientist / ML Engineer)

## Contexto

O pipeline de Free Flow evoluiu de um sistema de detecção e leitura de placas (YOLO + OCR) para um sistema completo de gestão de transações de pedágio. Isso exigiu a implementação de persistência de dados para:

1. **Rastrear transações:** Cada passagem de veículo deve ser registrada com timestamp, localização, placa lida, tipo de veículo detectado e valor cobrado.
2. **Cruzar dados:** O sistema precisa comparar a placa lida pelo OCR com a base de tags OBO para identificar divergências (ex: placa de carro com tag de moto, ou placa não cadastrada).
3. **Gerar relatórios de auditoria:** Transações com divergências devem ser sinalizadas para revisão humana.
4. **Calcular faturamento:** Agregações diárias de receita por status (pendente, divergência, não registrado).

Inicialmente, considerou-se manter tudo em memória ou usar arquivos CSV/JSON para simplicidade. No entanto, isso tornaria impossível realizar queries relacionais complexas (ex: "listar todas as divergências do pórtico X nos últimos 7 dias") e não suportaria concorrência em um cenário real de produção.

## Decisão

### 1. Escolha do SQLite como Banco de Dados
Optou-se pelo **SQLite** para o MVP local, apesar de saber que em produção seria melhor utilizar PostgreSQL ou similar.

**Racional:**
- **Zero configuração:** O SQLite não requer instalação de servidor, ideal para desenvolvimento e testes locais.
- **Suporte nativo no Python:** A biblioteca `sqlite3` está incluída na stdlib, sem dependências externas.
- **SQL completo:** Permite queries relacionais complexas, joins, índices e transações ACID.
- **Portabilidade:** O arquivo `.db` é um único arquivo que pode ser versionado (se pequeno) ou facilmente migrado.

**Trade-off aceito:**
- O SQLite não suporta alta concorrência de escrita (múltiplos processos escrevendo simultaneamente), o que seria um problema em produção com múltiplos pórticos. No entanto, para um MVP de portfólio, isso é aceitável.

### 2. Modelagem Relacional Normalizada
O schema foi projetado com **6 tabelas normalizadas** (3NF):

- `accounts`: Donos das tags OBO (clientes)
- `toll_categories`: Categorias de cobrança (carro, moto, caminhão)
- `toll_gates`: Pórticos/câmeras do Free Flow
- `vehicles`: Cadastro de veículos com placa
- `obo_tags`: Tags eletrônicas associadas a veículos e contas
- `transactions`: Registro de cada passagem (tabela de fatos)

**Racional:**
- **Integridade referencial:** Foreign keys garantem que uma transação sempre aponte para um pórtico válido, uma categoria válida, etc.
- **Evita redundância:** A categoria do veículo não é repetida em cada transação; é referenciada via `category_id`.
- **Facilita auditoria:** Divergências podem ser detectadas cruzando `transactions.plate_read` com `vehicles.plate` e comparando `transactions.vehicle_detected` com `toll_categories.vehicle_type`.

### 3. Arquitetura Modular (Separação em Múltiplos Arquivos)
O código do banco de dados foi dividido em **4 arquivos especializados**:

```
src/database/
── __init__.py          # Torna o pacote importável
├── connection.py        # Gerencia conexão e carrega schemas
├── schemas.sql          # DDL puro (CREATE TABLE, índices)
├── seed.sql             # DML de dados de exemplo (INSERTs)
└── repository.py        # Lógica de negócio (queries, CRUD)
```

**Racional:**
- **Separação de Responsabilidades (SoC):** O código que cria tabelas (DDL) não se mistura com o código que consulta dados (DML) ou com a lógica de conexão.
- **Portabilidade para Produção:** Se amanhã migrarmos para PostgreSQL, basta pegar o `schemas.sql` e rodar no novo banco. Se o SQL estivesse embutido em strings Python, a migração seria manual e propensa a erros.
- **Legibilidade para DBAs:** Arquivos `.sql` puros podem ser lidos, revisados e otimizados por qualquer pessoa ou ferramenta de banco de dados, sem precisar entender Python.
- **Code Review mais limpo:** Mudanças no schema alteram apenas `schemas.sql`. Mudanças na lógica de negócio alteram apenas `repository.py`. O Git diff fica claro e objetivo.
- **Testabilidade:** O `repository.py` pode ser testado unitariamente com mocks de conexão, sem precisar executar schemas.

## Consequências

### Positivas

1. **Sistema End-to-End Completo:** O projeto agora simula um pipeline real de Free Flow: Imagem → YOLO → OCR → Banco de Dados → Regras de Negócio → Auditoria.
2. **Detecção de Divergências Automatizada:** O sistema identifica automaticamente quando a placa lida difere da cadastrada na tag OBO, ou quando o tipo de veículo detectado (ex: moto) não bate com a categoria da tag (ex: carro).
3. **Preparado para Escala:** A arquitetura modular permite migrar para PostgreSQL com mínimo esforço. Os schemas estão prontos para serem rodados em qualquer banco relacional.
4. **Auditoria Transparente:** A tabela `transactions` com campo `divergence_reason` permite que operadores humanos revisem casos suspeitos, simulando o fluxo real de cobrança de pedágio.
5. **Código Profissional:** A separação em módulos demonstra maturidade de engenharia, algo que recrutadores técnicos valorizam muito.

### Negativas / Trade-offs

1. **Complexidade Adicional:** Para um projeto de portfólio, 4 arquivos podem parecer "exagero". No entanto, essa complexidade é justificada pela preparação para produção.
2. **SQLite não escala para produção real:** Em um cenário com 100+ pórticos escrevendo simultaneamente, o SQLite travaria. A migração para PostgreSQL seria obrigatória, mas o schema já está pronto para isso.
3. **Overhead de inicialização:** O sistema precisa carregar schemas e seed data na primeira execução, o que adiciona alguns segundos ao startup. Em produção, isso seria resolvido com migrations ferramentas como Alembic ou Flyway.
4. **Falta de Migrations Versionadas:** O schema atual é estático. Em produção, seria necessário implementar um sistema de migrations (ex: Alembic) para evoluir o schema sem perder dados.

## Alternativas Consideradas

### Alternativa 1: Tudo em um único arquivo `database.py`
**Prós:** Simplicidade inicial, menos arquivos para gerenciar.  
**Contras:** Código bagunçado, difícil de migrar para outro banco, SQL misturado com Python.  
**Por que foi rejeitada:** Não demonstra maturidade de engenharia e cria dívida técnica imediata.

### Alternativa 2: NoSQL (MongoDB)
**Prós:** Schema flexível, fácil de escalar horizontalmente.  
**Contras:** Perde a integridade referencial, queries relacionais complexas (joins) são difíceis, não é o padrão da indústria para sistemas financeiros/cobrança.  
**Por que foi rejeitada:** O Free Flow é inerentemente relacional (transações, categorias, tags, veículos). NoSQL seria um erro arquitetural.

### Alternativa 3: ORM (SQLAlchemy)
**Prós:** Abstração de banco, migrações automáticas, código mais "Pythonico".  
**Contras:** Adiciona dependência externa, curva de aprendizado, pode gerar queries ineficientes se mal utilizado.  
**Por que foi rejeitada:** Para um MVP, SQL puro é mais transparente e educativo. Em produção, SQLAlchemy seria uma boa adição.

## Referências

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Architecture Decision Records (ADRs)](https://adr.github.io/)
- [Martin Fowler - Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)