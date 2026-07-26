# FreeFlow Vision Pipeline

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-8.0+-purple.svg)](https://github.com/ultralytics/ultralytics)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Pipeline de Visao Computacional para simulacao de sistema **Free Flow** (pedagio eletronico sem parada) — deteccao e classificacao de veiculos com integracao futura a OCR de placas e banco de dados transacional.

---

## Objetivo

Detectar veiculos (carro/moto) em imagens de trafego, classifica-los, extrair a placa via OCR e montar transacoes de cobranca automatica com regras de negocio. O projeto simula a captura por cameras em porticos de rodovias.

---

## Estrutura do Repositorio

```
FreeFlow-Vision-Pipeline/
├── config/
│   └── settings.yaml              # Configuracoes do projeto (pendente)
├── data/                          # Dados auxiliares
├── datasets/
│   └── placas_brasileiras_10/     # Dataset YOLOv8 (Roboflow)
│       ├── data.yaml
│       ├── train/                 # 1.726 imagens + labels
│       ├── valid/                 # 493 imagens + labels
│       └── test/                  # 246 imagens + labels
├── env/
│   └── .env                       # Chave da API Roboflow
├── models/
│   └── best.pt                    # Pesos YOLOv8 treinados (22.5MB)
├── notebook/
│   └── FreeFlow_Vision_Pipeline.ipynb  # Notebook completo do projeto
├── outputs/
│   ├── predictions/               # Inferencias salvas
│   └── cropped_vehicles/          # Recortes de veiculos detectados
├── src/
│   ├── config.py                  # Constantes de path
│   ├── inference.py               # VehicleDetector (YOLO)
│   ├── business_rules.py          # Regras de negocio (placeholder)
│   ├── database.py                # Operacoes SQLite (placeholder)
│   ├── ocr_pipeline.py            # Pipeline de OCR (placeholder)
│   └── scripts/
│       ├── download_dataset.py    # Download via Roboflow
│       └── download_model.py      # Download dos pesos via GDrive
├── test_image/                    # Imagens para teste de inferencia
├── tests/
│   └── test_data_validator.py     # Testes (placeholder)
└── requirements.txt
```

---

## Stack Tecnologica

| Area | Ferramentas |
|---|---|
| Deteccao | Ultralytics YOLOv8, PyTorch |
| Visao Computacional | OpenCV, Supervision |
| Dados | Roboflow, Pandas, NumPy |
| Visualizacao | Matplotlib, Seaborn |
| Persistencia | SQLite |
| Ambiente | Google Colab (treino), Linux (inferencia) |

---

## Dataset

- **Fonte:** [Roboflow Universe — Alfascan / Placas Brasileiras v10](https://universe.roboflow.com/alfascan/placas_brasileiras/dataset/10)
- **Licenca:** BY-NC-SA 4.0
- **Classes:** `carro`, `moto`
- **Formato:** YOLOv8 (bbox + poligonos)
- **Distribuicao:**

| Conjunto | Imagens | Labels vazias (background) |
|---|---|---|
| Treino | 1.726 | 233 |
| Validacao | 493 | 57 |
| Teste | 246 | 36 |

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

O dataset e baixado do Roboflow (requer `env/.env` com a chave `roboflowApi`). O modelo `best.pt` e baixado do Google Drive.

---

## Uso — Inferencia

```python
from src.inference import VehicleDetector

detector = VehicleDetector(conf_threshold=0.05)

# Detectar veiculos em uma imagem
detections = detector.detect("test_image/GettyImages-2191972762.jpg")

for d in detections:
    print(f"{d['class_name']} — confianca: {d['confidence']:.2f}")

# Recortar veiculos detectados
for i, d in enumerate(detections):
    detector.crop_vehicle("test_image/GettyImages-2191972762.jpg", d['bbox'],
                          save_path=f"outputs/cropped_vehicles/crop_{i}.jpg")
```

Ou diretamente:

```bash
python src/inference.py
```

---

## Resultados do Treinamento

### Modelo Baseline (YOLOv8s, 50 epocas)

| Metrica | Valor |
|---|---|
| mAP@0.5 | 0.948 |
| mAP@0.5:0.95 | 0.823 |
| Precision | 0.875 |
| Recall | 0.941 |

| Classe | mAP@0.5 |
|---|---|
| Carro | 0.941 |
| Moto | 0.955 |

### Modelo Otimizado (balanced_yolov8s_v1, SGD, 80 epocas)

| Metrica | Valor |
|---|---|
| mAP@0.5 | 0.925 |
| mAP@0.5:0.95 | 0.795 |
| Precision | 0.902 |
| Recall | 0.896 |

> O modelo otimizado nao superou o baseline. A causa raiz identificada sao os **rotulos ruidosos** no dataset.

---

## Problemas Conhecidos

### 1. Rotulos Ruidosos

Imagens marcadas como "background" no dataset contem veiculos visiveis nao anotados. O modelo detecta veiculos em **100% dessas imagens** (814 deteccoes em 326 supostos backgrounds), inflando artificialmente os falsos positivos nas metricas.

### 2. Vies Espacial

**100% dos centroides** dos bounding boxes concentram-se na metade superior do frame (quadrante superior esquerdo). O modelo tem baixa generalizacao para veiculos em outras posicoes.

### 3. Ancoragem nas Placas

Os bounding boxes do dataset sao desenhados ao redor das **placas**, nao do veiculo inteiro. Se a placa estiver suja ou oclusa, o modelo pode perder o veiculo. A solucao proposta e ter dois detectores: um para veiculo (box amplo) e outro para placa (box apertado para OCR).

---

## Pipeline Completo (WIP)

```
[Captura] -> [Deteccao YOLO] -> [Classificacao carro/moto] -> [OCR da placa] -> [DB + Regras de negocio]
                                                                                      |
                                                                              [Transacao Free Flow]
```

---

## Roadmap

1. **Revisao do Dataset** — Reanotacao ou pseudo-labeling para corrigir rotulos ruidosos e vies espacial
2. **Pipeline de OCR** — Integracao com PaddleOCR/EasyOCR + Regex para validacao de placas (padrao Mercosul e antigo)
3. **Banco de Dados** — Implementar SQLite com tabelas `capturas`, `deteccoes`, `transacoes_freeflow`
4. **Regras de Negocio** — Classificacao tarifaria por tipo de veiculo, eixos e categoria
5. **Testes** — Implementar suite de testes automatizados
6. **API REST** — FastAPI para servir o modelo em producao
7. **Containerizacao** — Docker para deploy em ambientes Linux/cloud (AWS/GCP/Azure)

---

## Referencias

- [Ultralytics YOLOv8](https://docs.ultralytics.com/)
- [Roboflow Universe](https://universe.roboflow.com/)
- [Supervision](https://roboflow.github.io/supervision/)

---

<div align="center">

**Desenvolvido por Otavio Novais**
Cientista de Dados | Machine Learning Engineer
[LinkedIn](https://www.linkedin.com/in/otavio-novais/) | [GitHub](https://github.com/Otavio-Novais)

</div>
