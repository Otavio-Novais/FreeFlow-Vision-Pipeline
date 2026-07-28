# ADR-004: Arquitetura do Pipeline End-to-End e Separação de Responsabilidades

**Status:** Aceito  
**Data:** 2026-07-27  
**Decisores:** Otavio (Data Scientist / ML Engineer)

## Contexto
O projeto evoluiu de modelos isolados de Machine Learning (YOLOv8 para detecção e PaddleOCR para leitura) para um sistema que simula um cenário real de Free Flow. 

Um sistema de pedágio sem cancelas não pode se dar ao luxo de apenas "ler uma placa". Ele precisa tomar decisões de negócio em milissegulos com base em múltiplas fontes de dados:
1. A leitura visual da câmera (YOLO + OCR).
2. A leitura eletrônica da antena (Tecnologia OBO/RFID).
3. O cadastro prévio do veículo e sua categoria de pedágio.

Manter toda essa lógica (inferência de modelo, pré-processamento de imagem, queries SQL e regras de validação) em um único script ou notebook tornaria o código impossível de testar, manter ou escalar para um banco de dados de produção (como PostgreSQL).

## Decisão
Foi implementada uma arquitetura de **Monólito Modular** com clara Separação de Responsabilidades (Separation of Concerns), estruturada em três camadas principais orquestradas pela classe `FreeFlowPipeline`:

1. **Camada de Percepção (ML):** 
   - `VehicleDetector` (YOLOv8): Responsável apenas por localizar o veículo e retornar bounding boxes e classes.
   - `PlateOCR` (PaddleOCR): Responsável apenas por receber um recorte de imagem, aplicar pré-processamento e retornar o texto bruto e corrigido.
2. **Camada de Regras de Negócio e Persistência (Repository Pattern):** 
   - `TransactionRepository`: Isola toda a lógica SQL e de validação. O pipeline de ML não sabe como o banco de dados funciona; ele apenas chama `register_transaction()`.
   - Esta camada implementa uma máquina de estados para classificar a transação: `PENDING` (sucesso), `DIVERGENCE` (fraude ou erro de leitura), `UNREGISTERED` (sem tag, fluxo de boleto) ou `AUDIT` (tag inválida).
3. **Camada de Orquestração:** 
   - `FreeFlowPipeline`: Coordena o fluxo de dados, faz a normalização de classes (ex: mapear 'car' do YOLO para 'carro' do banco) e gerencia o ciclo de vida da execução.

## Consequências

### Positivas
1. **Testabilidade Unitária:** Ao isolar o `TransactionRepository`, foi possível criar testes unitários (`test_repository.py`) que validam 100% das regras de negócio (divergências, tags inativas, categorias desconhecidas) sem precisar carregar modelos pesados de GPU ou imagens.
2. **Prevenção de Evasão de Receita:** O sistema não apenas registra a passagem, mas ativamente cruza os dados. Se um caminhão (detectado pelo YOLO) passar com uma tag cadastrada como carro, o sistema automaticamente gera um alerta de `DIVERGENCE`, protegendo a concessionária.
3. **Portabilidade para Produção:** A orquestração está pronta para mudanças. Se a COMPSIS decidir migrar do SQLite local para um cluster PostgreSQL, ou trocar o YOLOv8 por um modelo customizado em TensorRT, apenas os módulos específicos precisam ser alterados, sem reescrever a lógica de negócio.
4. **Código Auto-documentado:** O uso de Type Hints, docstrings e nomes de variáveis expressivos reduz a necessidade de comentários excessivos e facilita o onboarding de novos desenvolvedores.

### Negativas / Trade-offs
1. **Processamento Síncrono:** O pipeline atual processa as etapas de forma sequencial (Detectar -> Recortar -> Ler -> Salvar). Em um cenário de altíssima vazão (ex: 3 faixas simultâneas a 100km/h), isso poderia se tornar um gargalo de latência. 
2. **Complexidade Inicial:** Para um observador casual, 4-5 arquivos para uma tarefa de "ler uma placa" podem parecer complexos demais comparados a um script único de 100 linhas.

## Alternativas Consideradas

### Alternativa 1: Script Monolítico (Estilo Notebook)
**Prós:** Desenvolvimento inicial extremamente rápido, menos arquivos.  
**Contras:** Impossível de testar unitariamente, acoplamento total entre ML e Banco de Dados, dívida técnica imediata.  
**Por que foi rejeitada:** Inviável para qualquer sistema que vise produção ou demonstre maturidade de engenharia.

### Alternativa 2: Arquitetura de Microsserviços com Message Broker (Kafka/RabbitMQ)
**Prós:** Escalabilidade horizontal massiva, processamento assíncrono, tolerância a falhas.  
**Contras:** Over-engineering (engenharia excessiva) para um projeto de portfólio/MVP. Adicionaria uma complexidade operacional (Docker Compose com múltiplos containers, configuração de brokers) que desviaria o foco da lógica de visão computacional e regras de negócio.  
**Por que foi rejeitada:** O Monólito Modular atende perfeitamente aos requisitos atuais. A arquitetura de microsserviços foi documentada como o **próximo passo evolutivo** caso o sistema seja levado para produção em escala na COMPSIS.

## Referências
- [Martin Fowler - Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- Documentação interna do projeto (ADRs 001, 002 e 003).