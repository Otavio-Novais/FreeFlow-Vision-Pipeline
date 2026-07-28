# ADR-005: Seleção e Configuração do Modelo de Detecção (YOLO26 Baseline)

**Status:** Aceito  
**Data:** 2026-07-28  
**Decisores:** Otavio (Data Scientist / ML Engineer)

## Contexto
Para a etapa de detecção e localização de veículos no pipeline Free Flow, foi selecionado o **YOLO26s** devido à sua arquitetura *NMS-free* (que reduz a latência de inferência em CPUs de borda) e alto desempenho.

Durante a fase de treinamento, foram conduzidos dois experimentos para definir a melhor configuração:
1. **Baseline:** Treinamento padrão de 50 epochs com hyperparameters default da Ultralytics.
2. **Optimized:** Treinamento com augmentações geométricas calibradas e hyperparameter tuning, visando maior generalização para diferentes ângulos e condições de iluminação.

O dataset utilizado (Roboflow/Alfascan) possui uma característica crítica: 326 imagens de "background" que contêm veículos não anotados (ruído de rotulação).

## Decisão
Adotar os pesos do **YOLO26s Baseline (melhor epoch: 47/49)** para o ambiente de produção. A versão "Optimized" foi descartada.

## Racional (Baseado em Dados Empíricos)

A decisão foi puramente orientada por dados. O modelo Baseline superou o Optimized em todas as métricas críticas de negócio:

| Métrica | YOLO26s Baseline | YOLO26s Optimized | Impacto no Negócio |
|---|---|---|---|
| **mAP@0.5** | **0.943** | 0.940 | Baseline localiza melhor a bounding box para o crop do OCR. |
| **mAP@0.5:0.95** | **0.817** | 0.796 | Baseline tem caixas mais precisas, evitando cortar letras da placa. |
| **Recall** | **0.920** | 0.906 | **Crítico:** Baseline deixa passar menos veículos (menos evasão de receita). |
| **Precision** | **0.906** | 0.873 | Baseline gera menos falsos positivos (ruído). |

### Por que o "Optimized" falhou?
A causa raiz da degradação no modelo Optimized foi o **ruído de rotulação do dataset**. 
As augmentações geométricas (translação, perspectiva) aplicadas no treinamento Optimized forçaram o modelo a olhar para as bordas da imagem. Como as imagens de "background" continham veículos não anotados nessas regiões, o modelo aprendeu a ignorar esses veículos ou a gerar falsos positivos em texturas de asfalto, piorando o Recall e a Precision.

O modelo Baseline, sendo mais conservador, focou nas regiões centrais (onde os veículos anotados estavam), generalizando melhor para a realidade física de um pórtico de pedágio (câmera fixa, veículo no centro da faixa).

## Consequências

### Positivas
- **Maximização da Receita:** Recall de 92.0% garante que a grande maioria dos veículos seja detectada e cobrada.
- **Estabilidade:** O modelo Baseline é menos sensível a ruídos de dataset, garantindo comportamento previsível em produção.
- **Latência Otimizada:** A arquitetura YOLO26 *NMS-free* garante que o tempo de inferência seja mínimo, mesmo em hardware de borda.

### Negativas / Próximos Passos
- **Teto de Performance:** O modelo não atingirá mAP > 0.96 sem uma curadoria manual do dataset (re-rotular as 326 imagens de background).
- **Confusão de Classes:** A matriz de confusão indica que ~44% das motos são classificadas como carros. Em produção, isso pode gerar cobrança na tarifa errada. O próximo passo é aplicar *Class Balancing* ou *Oversampling* para a classe "Moto".

## Referências
- [Ultralytics YOLO26 Documentation](https://docs.ultralytics.com/models/yolo26/)
- Dados brutos de treinamento: `results_yolo26s.csv` e `results_optimized_YOLO26.csv`.
- [ADR-001](001-spatial-bias-handling.md) (Tratamento de Viés Espacial e Ruído de Dataset).