# ADR-005: Seleção do Modelo de Detecção de Veículos (YOLO26)

**Status:** Aceito  
**Data:** 2026-07-28  
**Decisores:** Otavio (Data Scientist / ML Engineer)

## Contexto
Para dar início ao projeto, era necessário definir um modelo de visão computacional para a etapa de **detecção e localização de veículos** (que antecede o recorte e a leitura de placas via OCR). O ambiente de produção alvo (pórticos de pedágio Free Flow) impõe restrições críticas:
1. **Baixa Latência:** O processamento deve ser rápido para lidar com veículos em alta velocidade.
2. **Hardware de Borda (Edge):** Muitos pórticos utilizam CPUs ou GPUs de entrada, exigindo modelos otimizados.
3. **Alto Recall:** Falsos negativos significam evasão de receita (o carro passa e não é cobrado).

Foram avaliadas as seguintes arquiteturas do estado da arte (SOTA):
1. **YOLOv8 / YOLO11:** Padrões atuais da indústria, excelentes em velocidade e acurácia.
2. **YOLOv9 / v10 / YOLO26:** Iterações mais recentes com foco em eficiência e remoção de pós-processamento.
3. **RT-DETR (Real-Time DEtection TRansformer):** Abordagem baseada em Transformers, forte em acurácia, mas pesada computacionalmente.
4. **DETR / Faster R-CNN:** Modelos de dois estágios (Two-Stage). Altíssima precisão, mas latência inaceitável para tempo real.
5. **SSD (Single Shot MultiBox Detector):** Arquitetura clássica, mas superada em acurácia pelas versões modernas do YOLO.

## Decisão
Optou-se pelo **YOLO26 (versão 's' - small)** como o motor de detecção principal do pipeline.

## Racional
A escolha do YOLO26 sobre as alternativas baseia-se em três pilares de engenharia de produção:

1. **Inferência End-to-End NMS-Free:** 
   Diferente do YOLOv8 e modelos mais antigos, o YOLO26 elimina a necessidade de *Non-Maximum Suppression* (NMS) externo em Python/C++. O NMS é um gargalo de pós-processamento que consome CPU. Ao embutir essa lógica na rede, o YOLO26 reduz a latência total de inferência, o que é crucial para o throughput do pórtico.

2. **Otimização para Edge Computing:**
   A arquitetura do YOLO26 foi desenhada para rodar eficientemente em hardware limitado (CPUs e NPUs de borda). Em um cenário real de concessionária, onde nem todo pórtico possui GPUs de última geração (ex: NVIDIA A100), o YOLO26 's' oferece o melhor trade-off entre velocidade e acurácia.

3. **Resultados Empíricos no Dataset (Baseline):**
   O treinamento baseline (50 epochs) atingiu métricas robustas para o cenário de negócio:
   - **Recall: 0.935** (Priorizado para minimizar evasão de receita).
   - **mAP@0.5: 0.933** (Alta precisão na localização da bounding box para o crop do OCR).
   - **mAP@0.5:0.95: 0.787** (Boa precisão de caixa, garantindo que o recorte para o OCR não corte as letras da placa).

### Por que rejeitamos as outras opções?
- **Faster R-CNN / DETR:** Descartados por serem *Two-Stage*. A latência de inferência é muito alta para um fluxo de 100 km/h.
- **RT-DETR:** Embora poderoso, seu consumo de memória e dependência de hardware mais robusto o tornam menos flexível para implantação em massa em pórticos legados.
- **SSD:** Acurácia inferior aos modelos YOLO modernos, resultaria em mais falsos negativos.
- **YOLOv8 / YOLO11:** Excelentes alternativas. A migração para o YOLO26 foi motivada especificamente pela arquitetura *NMS-free* e otimizações de inferência em CPU.

## Consequências

### Positivas
- **Redução de Latência:** A remoção do NMS externo acelera o pipeline, permitindo processar mais veículos por segundo.
- **Facilidade de Deploy:** Modelos menores e otimizados para CPU facilitam a containerização (Docker) e o deploy em servidores de borda.
- **Alto Recall:** A taxa de 93.5% de recall garante que a grande maioria dos veículos seja detectada, protegendo a receita da concessionária.

### Negativas / Trade-offs
- **Maturidade da Comunidade:** Por ser uma versão mais recente (bleeding edge), o YOLO26 possui menos tutoriais, issues no GitHub e suporte da comunidade comparado ao YOLOv8.
- **Dependência do Ecossistema Ultralytics:** O projeto fica atrelado às atualizações e mudanças de API da Ultralytics.
- **Overfitting em Datasets Ruidosos:** Assim como no YOLOv8, o YOLO26 mostrou sensibilidade a augmentações geométricas agressivas devido ao *spatial bias* e ruídos do dataset (ver [ADR-001](001-spatial-bias-handling.md)).

## Referências
- [Ultralytics YOLO26 Documentation](https://docs.ultralytics.com/models/yolo26/)
- [Real-Time Detection Transformers (RT-DETR)](https://arxiv.org/abs/2304.08069)
- Resultados de treinamento: `results_yolo26s.csv` (Melhor epoch: 38).