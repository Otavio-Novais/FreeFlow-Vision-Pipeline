# ADR-001: Tratamento de Viés Espacial (Spatial Bias) no Treinamento do YOLOv8

**Status:** Aceito
**Data:** 2026-07-25
**Decisores:** Otavio (Data Scientist / ML Engineer)

## Contexto
Durante a Análise Exploratória de Dados (EDA) do dataset de veículos, identificou-se um forte viés espacial (spatial bias): 80% das bounding boxes estavam concentradas na região superior-central da imagem (cy entre 0.2 e 0.5).

A abordagem inicial de engenharia de dados foi tentar "corrigir" esse viés aplicando augmentações geométricas agressivas (`translate=0.3`, `perspective=0.001`, `scale=0.9`) para forçar o modelo a generalizar para os cantos da imagem.

## Decisão
**Reverter as augmentações geométricas agressivas e manter o viés espacial.** 
O modelo foi retreinado com augmentações focadas estritamente em variações fotométricas (HSV, CLAHE) e geométricas leves (`translate=0.05`), respeitando a física do cenário de Free Flow.

## Consequências

### Positivas
- **Aderência à Realidade Física:** Em um pórtico de pedágio real, a câmera é fixa e os veículos sempre passam pelo centro da faixa. O viés espacial não é um "defeito" do dataset, é a representação exata do ambiente de produção.
- **Performance do Modelo:** O modelo "otimizado" com augmentações agressivas sofreu degradação de mAP50-95 (de 82.4% para ~75%), pois aprendeu a detectar veículos em posições fisicamente impossíveis (ex: canto inferior esquerdo), gerando falsos positivos em sombras e texturas de asfalto.
- **Estabilidade:** O modelo final (Balanced) convergiu mais rápido (Early Stopping) e mostrou maior estabilidade na matriz de confusão.

### Negativas / Trade-offs
- **Falta de Generalização para Outros Domínios:** Se esse modelo for implantado em uma câmera de celular (como em um app de fiscalização), ele terá baixa performance, pois não aprendeu a detectar veículos em ângulos ou posições atípicas. O modelo é estritamente especializado para câmeras de pórtico fixas.