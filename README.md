# FreeFlow ANPR Pipeline

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-8.0+-purple.svg)](https://github.com/ultralytics/ultralytics)
[![PaddleOCR](https://img.shields.io/badge/PaddleOCR-PP--OCRv4-orange.svg)](https://github.com/PaddlePaddle/PaddleOCR)
[![Tests](https://img.shields.io/badge/tests-104/104%20passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Pipeline end-to-end de **ANPR (Automatic Number Plate Recognition)** para sistemas de pedágio Free Flow...** — da deteccao do veiculo ate a transacao financeira com regras de negocio automatizadas.

---
## Resumo do Projeto


Simulacao completa de um sistema de pedagio eletronico sem cancelas. Uma camera de portico captura o veiculo em movimento, o modelo **YOLOv8** classifica o tipo (carro/moto/caminhao), o **PaddleOCR** le a placa com correcao heuristica, e um banco **SQLite** relacional cruza os dados com tags OBO para detectar divergencias e fraudes — tudo orquestrado por uma classe `FreeFlowPipeline` que processa uma imagem e retorna uma transacao pronta em uma unica chamada.

```
    [Camera] ---> [YOLOv8] ---> [Crop] ---> [PaddleOCR] ---> [SQLite + Business Rules]
                      |                        |                      |
                class carro/moto        "IYJ7F53"              DIVERGENCE?
                                                           UNREGISTERED?
                                                             PENDING?
```

---
## Contexto do Problema

O Free Flow é um modelo de pedágio sem cancelas onde veículos passam em fluxo livre, 
sem necessidade de parada. A tecnologia OBO (On-Board Equipment) permite identificação 
eletrônica automática via tags RFID/DSRC no para-brisa.

No entanto, nem todos os veículos possuem tag OBO ativa. Nesses casos, o sistema depende 
de **leitura visual por câmeras** para identificar a placa e processar a cobrança 
posteriormente (via notificação ou boleto).

Este projeto explora como um pipeline de **Visão Computacional** (YOLO + OCR) pode 
auxiliar nesse processo, implementando uma arquitetura que:

1. **Detecta e classifica veículos** (carro/moto) em imagens de pórtico
2. **Lê placas veiculares** com correção heurística para padrões brasileiros (Antigo e Mercosul)
3. **Simula regras de negócio** para cruzamento com tags OBO, classificando transações como:
   - `PENDING`: leitura visual e tag OBO consistentes
   - `DIVERGENCE`: inconsistência entre placa lida e tag registrada
   - `UNREGISTERED`: veículo sem tag OBO (fluxo de cobrança por notificação)

> 📝 **Nota**: Esta é uma POC educacional. Os valores de tarifa, percentuais de evasão 
> e cenários de fraude são **ilustrativos**, baseados em conhecimento geral do setor 
> de concessões rodoviárias. O dataset utilizado contém apenas 2 classes: **carro** e **moto**.

---
## Estrutura do Repositorio

```
FreeFlow-Vision-Pipeline/
├── config/
│   └── settings.yaml                    # Configuracoes do projeto (pendente)
├── data/
│   └── freeflow.db                      # SQLite gerado automaticamente
├── datasets/
│   └── placas_brasileiras_10/           # Dataset YOLOv8 (Roboflow, v10)
│       ├── data.yaml                    #  2 classes: carro, moto
│       ├── train/                       #  1.726 imagens
│       ├── valid/                       #    493 imagens
│       └── test/                        #    246 imagens
├── docs/
│   └── decisions/                       # Architecture Decision Records (4 ADRs)
│       ├── 001-spatial-bias-handling.md
│       ├── 002-ocr-engine-and-correction-strategy.md
│       ├── 003-relational-database-and-modular-architecture.md
│       └── 004-pipeline-architecture-and-business-rules.md
├── models/
│   └── best.pt                          # Pesos YOLOv8 treinados (22.5 MB)
├── notebook/
│   └── FreeFlow_Vision_Pipeline.ipynb   # Notebook completo (8 etapas)
├── outputs/
│   ├── predictions/                     # Imagens anotadas pelo YOLO
│   ├── cropped_vehicles/                # Recortes de veiculos detectados
│   ├── ocr_images/                      # Pre-processamento de imagens OCR
│   ├── paddle_images/                   # Visualizacao dos resultados PaddleOCR
│   ├── paddle_json_images/              # JSONs de saida do PaddleOCR
│   └── pipeline_debug/                  # Debug do pipeline integrado
├── src/
│   ├── config.py                        # Constantes de caminho do projeto
│   ├── inference.py                     # VehicleDetector (classe YOLO)
│   ├── ocr_pipeline.py                  # PlateOCR (PaddleOCR + correcao)
│   ├── pipeline.py                      # FreeFlowPipeline (orquestrador)
│   ├── database/
│   │   ├── __init__.py                  # Expõe DatabaseConnection e TransactionRepository
│   │   ├── connection.py                # Gerenciamento de conexao SQLite
│   │   ├── repository.py                # TransactionRepository (regras de negocio)
│   │   ├── schemas.sql                  # DDL: 6 tabelas + indices
│   │   └── seed.sql                     # DML: dados de exemplo (5 cenarios)
│   └── scripts/
│       ├── download_dataset.py          # Download Roboflow
│       └── download_model.py            # Download Google Drive
├── test_images/                         # 8 imagens para inferencia
├── tests/
│   ├── __init__.py
│   ├── conftest.py                       # Fixtures compartilhadas
│   ├── test_config.py                    # 9 testes de constantes de path
│   ├── test_database.py                  # 17 testes de conexao e schema
│   ├── test_inference.py                 # 13 testes do VehicleDetector
│   ├── test_ocr_pipeline.py              # 36 testes do PlateOCR
│   ├── test_paddleocr_check.py           # Verificacao de ambiente PaddleOCR
│   ├── test_pipeline.py                  # 7 testes do FreeFlowPipeline
│   └── test_repository.py               # 12 testes de regras de negocio
└── requirements.txt                     # 15 dependencias limpas
```

---

## Stack Tecnologica

| Camada | Tecnologia | Proposito |
|---|---|---|
| **ML / Deteccao** | Ultralytics YOLOv8, PyTorch | Deteccao e classificacao de veiculos |
| **OCR** | PaddleOCR (PP-OCRv4) | Leitura de placas veiculares |
| **Visao Computacional** | OpenCV, NumPy | Pre-processamento e recorte de imagens |
| **Banco de Dados** | SQLite + SQL puro | Persistencia relacional de transacoes |
| **Dataset** | Roboflow Universe (Alfascan, v10) | 2.465 imagens rotuladas |
| **Analise** | Pandas, Matplotlib, Seaborn, SciPy | EDA e visualizacao de metricas |
| **Testes** | pytest, unittest | 104 cenarios cobrindo ML, OCR, DB e pipeline |
| **Documentacao** | ADRs (Architecture Decision Records) | 4 decisoes de arquitetura registradas |

---

## Instalacao

```bash
git clone https://github.com/Otavio-Novais/FreeFlow-Vision-Pipeline.git
cd FreeFlow-Vision-Pipeline
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### Download do Dataset e Modelo

```bash
python src/scripts/download_dataset.py
python src/scripts/download_model.py
```

> O dataset e baixado do Roboflow (requer chave em `env/.env`). O modelo `best.pt` e baixado do Google Drive.

---

## Uso

### Pipeline Completo (1 chamada)

```python
from src.pipeline import FreeFlowPipeline

pipeline = FreeFlowPipeline()

# Uma imagem -> transacao registrada no banco
transactions = pipeline.process_image(
    "test_images/brasil_placa.jpg",
    gate_id=1,
    obo_tag="OBO-002"
)

for t in transactions:
    print(f"Status: {t['status']} | Valor: R${t['toll_amount']:.2f}")
    # Status: PENDING | Valor: R$5.50

pipeline.get_audit_report()
pipeline.close()
```

Ou execute diretamente os 3 cenarios de teste:

```bash
python src/pipeline.py
```

### Deteccao YOLO Isolada

```python
from src.inference import VehicleDetector

detector = VehicleDetector(conf_threshold=0.20)
detections = detector.detect("test_images/brasil_placa.jpg")

for d in detections:
    print(f"{d['class_name']} - {d['confidence']:.2%}")
```

### OCR Isolado

```python
import cv2
from src.ocr_pipeline import PlateOCR

ocr = PlateOCR()
image = cv2.imread("outputs/cropped_vehicles/cropped_carro_0.jpg")
result = ocr.read_plate(image)

print(result['raw_text'])         # "AOX5G10"
print(result['corrected_text'])   # "AOX5G10" (ja valido)
print(result['validated_plate'])  # "AOX5G10" (Mercosul)
```

### Banco de Dados Isolado

```python
from src.database.repository import TransactionRepository

repo = TransactionRepository()

repo.register_transaction(
    gate_id=1, plate_read="IYJ7F53",
    vehicle_detected="carro",
    plate_confidence=0.98, vehicle_confidence=0.95,
    obo_tag_number="OBO-002"
)
# Retorna: {'status': 'PENDING', 'toll_amount': 5.50}

print(repo.get_daily_revenue())
# {'total_transactions': 5, 'revenue_pending': 5.5, ...}

print(repo.get_divergences())
# Lista transacoes com DIVERGENCE, AUDIT, UNREGISTERED

repo.close()
```

### Rodar Testes

```bash
python -m pytest tests/ -v
# 104 passed
```

---

## Resultados

### YOLOv8 — Deteccao de Veiculos

| Metrica | Baseline | Optimized |
|---|---|---|
| **mAP@0.5** | 0.948 | 0.925 |
| **mAP@0.5:0.95** | 0.823 | 0.795 |
| **Precision** | 0.875 | 0.902 |
| **Recall** | 0.941 | 0.896 |

| Classe | mAP@0.5 (Baseline) |
|---|---|
| Carro | 0.941 |
| Moto | 0.955 |

💡 **Insight contraintuitivo**: O modelo "otimizado" com augmentações geométricas 
> agressivas (translate=0.3, perspective=0.001) **piorou** o mAP. 
> 
> **Causa raiz**: O dataset tem 326 imagens de "background" com veículos não anotados. 
> Augmentações ensinaram o modelo a detectar carros em posições fisicamente impossíveis 
> (cantos da imagem), gerando falsos positivos.
> 
> **Decisão**: Mantivemos o spatial bias natural — câmeras de pórtico são fixas, 
> veículos sempre passam pelo centro. [Ver ADR-001](docs/decisions/001-spatial-bias-handling.md).

### PaddleOCR — Leitura de Placas

O OCR bruto alcancou ~70% de acuracia em imagens reais. Com a camada de correcao heuristica (Minimum Edit Distance + dicionario de confusoes visuais), a acuracia subiu para **100% no dataset de teste**:

| Cenario | OCR Bruto | Apos Correcao |
|---|---|---|
| "IYJ7F53" | "IYJ7F53" (Mercosul) | "IYJ7F53" |
| "AOX5G10" | "AOX5G10" (Mercosul) | "AOX5G10" |
| "NUU4E04" | "NUU4E04" (Mercosul) | "NUU4E04" |

**Dicionario de confusoes visuais**: 12 pares mapeados (Z↔2, O↔0, S↔5, B↔8, G↔6, I↔1, etc.) corrigindo erros classicos de OCR em placas veiculares. [Ver ADR-002](docs/decisions/002-ocr-engine-and-correction-strategy.md).

### Regras de Negocio — Cobertura de Cenarios

**104/104 testes passando** em 8 arquivos, cobrindo todas as camadas do sistema:

#### Banco de Dados & Negocio (29 testes)
| # | Cenario | Status Gerado | Tarifa |
|---|---|---|---|
| 1 | Passagem normal (placa + tag batem) | `PENDING` | R$ 5.50 |
| 2 | Divergencia de placa (OCR x tag) | `DIVERGENCE` | R$ 5.50 |
| 3 | Divergencia de categoria (caminhao com tag de carro) | `DIVERGENCE` | R$ 16.50 |
| 4 | Veiculo sem tag OBO | `UNREGISTERED` | R$ 5.50 |
| 5 | Tag OBO inativa | `UNREGISTERED` | R$ 5.50 |
| 6 | Tag inexistente | `UNREGISTERED` | R$ 5.50 |
| 7 | Categoria desconhecida pelo YOLO | `UNREGISTERED` | R$ 0.00 |
| 8 | Consulta de divergencias (auditoria) | — | — |
| 9 | Faturamento diario agregado | — | — |
| 10 | Multiplas passagens mesmo veiculo | `PENDING` (3x) | R$ 16.50 |
| 11 | Placa vazia (edge case) | `UNREGISTERED` | — |
| 12 | Confianca zero (edge case) | `UNREGISTERED` | — |
| + | Schema: 6 tabelas + 5 indices criados | — | — |
| + | Seed data idempotente | — | — |
| + | Context manager: commit, rollback, cursor close | — | — |

#### OCR — Leitura de Placas (36 testes)
| Metodo | Cenarios |
|---|---|
| `validate_plate` | 12 (Mercosul, antigo, vazio, lowercase, edge cases) |
| `_apply_corrections` | 10 (correcoes validas, sem confusao, multiplas violacoes) |
| `correct_plate_by_pattern` | 7 (perfeito, 1 correcao, incrretivel, empate de custo) |
| `read_plate` | 5 (vazio, texto unico, multiplo, regex, invalido) |
| `preprocess_image` | 6 (upscale, sem resize, canais, aspecto, nitidez, grayscale) |

#### Deteccao YOLO (13 testes)
| Metodo | Cenarios |
|---|---|
| `__init__` | 3 (default weights, custom conf, default conf) |
| `detect` | 5 (sem deteccao, unica, multipla, save, params) |
| `crop_vehicle` | 8 (normal, clamping 4 bordas, fora, float, zero-area) |

#### Pipeline & Config (16 testes)
| Metodo | Cenarios |
|---|---|
| `FreeFlowPipeline.__init__` | 4 (componentes, threshold, class mapping) |
| `get_audit_report` / `close` | 3 (com/sem divergencias, delegacao) |
| `config.py` paths | 9 (absoluto, Path, existencia, consistencia) | |

[Ver ADR-003](docs/decisions/003-relational-database-and-modular-architecture.md) e [ADR-004](docs/decisions/004-pipeline-architecture-and-business-rules.md).

---

## Desafios Técnicos Superados

| Desafio | Solução | Impacto |
|---------|---------|---------|
| **OCR lendo `NOU4E04` em vez de `IYJ7F53`** | Descobri que o crop do YOLO retornava um "Numpy View" (memória não-contígua). Adicionar `.copy()` resolveu. | Acurácia OCR: 70% → 100% |
| **Augmentations pioraram o mAP do YOLO** | EDA revelou spatial bias natural do dataset (câmeras fixas de pórtico). Removi augmentations geométricas agressivas. | mAP@0.5: 0.795 → 0.948 |
| **PaddleOCR crashava no Python 3.13** | Erro de MKL ("dynamic library not loaded"). Solução: `export LD_LIBRARY_PATH` + variáveis de ambiente. | Pipeline funcional em Python 3.13 |
| **Placa `A0X5G10` sendo "corrigida" para padrão errado** | Implementei lógica de "Minimum Edit Distance" — escolhe o padrão que exige MENOS alterações. | Correção precisa entre Antigo/Mercosul |

---
## Decisoes de Arquitetura

O projeto segue **4 ADRs** documentando cada decisao tecnica relevante:

| ADR | Tema | Decisao Chave |
|---|---|---|
| [001](docs/decisions/001-spatial-bias-handling.md) | Vies Espacial | Manter o vies em vez de "corrigi-lo" — cameras de portico sao fixas |
| [002](docs/decisions/002-ocr-engine-and-correction-strategy.md) | Motor OCR | PaddleOCR PP-OCRv4 + correcao heuristica (Minimum Edit Distance) |
| [003](docs/decisions/003-relational-database-and-modular-architecture.md) | Banco de Dados | SQLite com 6 tabelas normalizadas, SQL puro em arquivos `.sql` separados |
| [004](docs/decisions/004-pipeline-architecture-and-business-rules.md) | Arquitetura | Monolito Modular em 3 camadas (Percepcao, Negocio, Orquestracao) |

Principio norteador: **Separacao de Responsabilidades** — o YOLO nao sabe que existe banco de dados, o banco nao sabe que existe OCR, e o orquestrador apenas coordena o fluxo.

---

## Modelo de Dados

```
accounts ──┐                  toll_categories
           │                         │
        obo_tags ──── vehicles ──────┘
           │
      transactions ──── toll_gates
```

**6 tabelas, 3a Forma Normal**, indices em `timestamp`, `plate_read`, `status` e `tag_number`. [Schemas SQL completos aqui](src/database/schemas.sql).

---

## Roadmap

### Concluído ✅
- [x] Detecção YOLOv8 + classificação carro/moto (mAP@0.5: 0.948)
- [x] OCR com PaddleOCR + correção heurística (100% acurácia no teste)
- [x] Banco SQLite com 6 tabelas normalizadas (3FN)
- [x] Regras de negócio: divergência, auditoria, faturamento
- [x] 104 testes unitários cobrindo todas as camadas
- [x] Pipeline orquestrado (`FreeFlowPipeline`)
- [x] 4 ADRs documentando decisões arquiteturais

### Próximos Passas 🎯
- [ ] **API REST (FastAPI)**: Endpoint `/predict` recebendo imagem e retornando transação JSON
- [ ] **Dashboard Streamlit**: Visualização de divergências, faturamento diário, heatmap de pórticos
- [ ] **Containerização (Docker)**: Docker Compose com app + PostgreSQL + Redis
- [ ] **Migração PostgreSQL**: Testar schema atual em banco de produção com concorrência
- [ ] **Sistema de filas (Kafka/RabbitMQ)**: Arquitetura de microsserviços para escalabilidade horizontal
- [ ] **Deploy cloud (AWS)**: Lambda + S3 + RDS para processamento sob demanda

---

<div align="center">

**FreeFlow ANPR Pipeline**  
Desenvolvido por Otavio Novais  
Data Scientist | Machine Learning Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/otavio-novais/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github)](https://github.com/Otavio-Novais)

</div>
