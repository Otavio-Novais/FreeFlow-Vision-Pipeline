# 🚗 FreeFlow Vision Pipeline - Detecção de Veículos para Sistemas de Pedágio Livre

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-8.0+-purple.svg)](https://github.com/ultralytics/ultralytics)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 Sobre o Projeto

O **FreeFlow Vision Pipeline** é um projeto de Ciência de Dados e Visão Computacional focado no desenvolvimento de um sistema de detecção e classificação de veículos para cenários de **Free Flow** (pedágio eletrônico em livre passagem). 

O sistema simula a captura de veículos em alta velocidade através de câmeras em pórticos, utilizando Deep Learning para identificar e classificar o tipo de veículo (Carro/Moto), preparando a arquitetura para a integração com sistemas de OCR (leitura de placas) e regras de negócio de cobrança.

## 🌍 Contexto de Negócio: O Desafio do Free Flow

Em sistemas de pedágio sem parada, a precisão da Visão Computacional impacta diretamente a receita e a experiência do usuário. O projeto foi desenhado para resolver os principais desafios deste domínio:

*   **Redução de Falsos Positivos:** Evitar que sombras, asfalto ou objetos na via sejam classificados erroneamente como veículos, o que geraria cobranças indevidas.
*   **Precisão no Recorte (Bounding Box Tightness):** Garantir que a caixa delimitadora do veículo seja precisa para que, em um pipeline real, o recorte da imagem para o OCR não contenha ruídos do entorno.
*   **Integração com OBO (On-Board Equipment):** Preparar a estrutura de dados para cruzar a classificação visual (ex: Moto) com os dados da tag eletrônica do veículo, identificando divergências e possíveis fraudes.

## 🛠️ Stack Tecnológica

### Core ML & Visão Computacional
*   **Python 3.8+**
*   **Ultralytics YOLOv8** (Detecção de objetos em tempo real)
*   **PyTorch** (Backend de Deep Learning)
*   **OpenCV** & **Supervision** (Processamento de imagens e visualização de detecções)

### Data Engineering & MLOps
*   **Roboflow** (Versionamento, pré-processamento e gerenciamento de datasets)
*   **Pandas & NumPy** (Manipulação e análise de dados)
*   **Matplotlib & Seaborn** (EDA e visualização de métricas)
*   **SQLite** (Persistência de dados e simulação de transações)
*   **Google Colab** (Ambiente de experimentação e treino)

## 📊 Dataset

*   **Fonte:** Roboflow Universe (Alfascan - Placas Brasileiras)
*   **Licença:** BY-NC-SA 4.0
*   **Classes:** `Carro` e `Moto`
*   **Formato:** YOLOv8 (Suporte nativo a anotações em polígono e bounding box)
*   **Split:** ~1.726 imagens de treino, ~246 de validação e ~246 de teste.
*   **Pré-processamento:** Auto-orient e Resize (Stretch to 640x640).

## 🏗️ Arquitetura do Pipeline

O projeto é estruturado em um pipeline de dados modular, seguindo as melhores práticas de MLOps:

```text
[ Aquisição ] ➔ [ Validação & EDA ] ➔ [ Treinamento (YOLOv8) ] ➔ [ Inferência ] ➔ [ Persistência (SQL) ]
```

1. **Aquisição e Validação:** Download via API, verificação de integridade (imagens vs. labels) e tratamento de anotações complexas (polígonos para bbox).
2. **EDA (Análise Exploratória):** Distribuição de classes, análise de amostras negativas (background) e visualização de bounding boxes.
3. **Treinamento:** Transfer Learning com YOLOv8s, ajuste de hiperparâmetros e monitoramento de métricas (mAP, Precision, Recall).
4. **Inferência e Regras de Negócio:** Detecção em novas imagens, extração de metadados e estruturação para montagem de transações.

## 📁 Estrutura do Repositório

```text
FreeFlow_Vision_Pipeline/
── datasets/                 # Datasets versionados (via Roboflow)
├── models/                   # Pesos treinados (.pt) e logs do YOLO
├── notebooks/                # Notebooks de EDA, Treino e Inferência
├── src/                      # Scripts modulares (data_validation, eda, inference)
├── results/                  # Visualizações, métricas e relatórios
├── README.md
└── requirements.txt
```

## 🚀 Como Executar

### 1. Instalação
```bash
git clone https://github.com/seu-usuario/FreeFlow_Vision_Pipeline.git
cd FreeFlow_Vision_Pipeline
pip install -r requirements.txt
```

### 2. Download do Dataset
```python
from roboflow import Roboflow

rf = Roboflow(api_key="SUA_API_KEY")
project = rf.workspace("alfascan").project("placas_brasileiras")
dataset = project.version(11).download("yolov8")
```

### 3. Treinamento do Modelo (Baseline)
```python
from ultralytics import YOLO

model = YOLO('yolov8s.pt')
results = model.train(
    data='datasets/placas_brasileiras-11/data.yaml',
    epochs=50,
    imgsz=640,
    batch=16,
    project='models',
    name='baseline_yolov8s'
)
```

## 🔍 Desafios Técnicos e Soluções

### 1. Conversão de Polígonos para Bounding Boxes
**Problema:** O dataset original continha anotações em formato de polígono (4 pontos) para maior precisão em placas em perspectiva, o que não é nativamente suportado pelo formato padrão de treino do YOLOv8.
**Solução:** Desenvolvimento de um algoritmo de conversão que calcula o *Minimum Bounding Box* (caixa delimitadora mínima) envolvendo todos os vértices do polígono, garantindo a compatibilidade com o modelo sem perda crítica de contexto.

### 2. Tratamento de Amostras Negativas (Background)
**Problema:** O dataset continha centenas de imagens sem veículos (apenas cenário de fundo).
**Solução:** Em vez de descartar esses dados, foram mantidos no pipeline de treino. Isso é crucial para ensinar o modelo a identificar a ausência de objetos, reduzindo drasticamente a taxa de **Falsos Positivos** em cenários de ruas vazias.

## 📈 Resultados (Baseline YOLOv8s)

*Nota: Preencher após a conclusão do treinamento.*

| Métrica | Valor |
|---------|-------|
| **mAP@0.5** | *Aguardando treino...* |
| **mAP@0.5:0.95** | *Aguardando treino...* |
| **Precision** | *Aguardando treino...* |
| **Recall** | *Aguardando treino...* |

## 🔮 Roadmap e Próximos Passos

*   **Fase 1 (Otimização):** Teste de arquiteturas (YOLOv8n vs YOLOv8m), ajuste fino de *Data Augmentation* para simular condições adversas (chuva, baixa luminosidade) e análise de *Focal Loss* para desbalanceamento de classes.
*   **Fase 2 (Pipeline de OCR):** Integração com modelos de reconhecimento óptico (ex: PaddleOCR ou EasyOCR) para extração de texto das placas detectadas.
*   **Fase 3 (Lógica de Negócio e OBO):** Implementação de banco de dados relacional para simular o cruzamento de dados entre a Visão Computacional e dispositivos OBO (tags), criando regras de auditoria para divergências de categoria.
*   **Fase 4 (MLOps & Deploy):** Criação de uma API REST (FastAPI), containerização com Docker e preparação para deploy em ambientes Linux/Edge Computing.

## 📚 Referências

*   [Ultralytics YOLOv8 Documentation](https://docs.ultralytics.com/)
*   [Roboflow Universe](https://universe.roboflow.com/)
*   [Supervision Library](https://roboflow.github.io/supervision/)

---

<div align="center">

**Desenvolvido por Otávio Novais**  
Cientista de Dados | Machine Learning Engineer  
[LinkedIn](https://www.linkedin.com/in/otavio-novais/) | [GitHub](https://github.com/Otavio-Novais)

</div>