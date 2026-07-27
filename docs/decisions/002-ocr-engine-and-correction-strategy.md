# ADR-002: Seleção do Motor de OCR e Estratégia de Correção Heurística

**Status:** Aceito
**Data:** 2026-07-27
**Decisores:** Otavio (Data Scientist / ML Engineer)

## Contexto
O pipeline de Free Flow exige a leitura precisa de placas de veículos brasileiros, que podem estar no formato Antigo (LLL-NNNN) ou Mercosul (LLLNLNN). As imagens de entrada apresentam variações de iluminação, perspectiva e qualidade (domain shift).

Inicialmente, o EasyOCR foi selecionado por sua facilidade de integração. No entanto, testes em produção (imagens não vistas) revelaram falhas críticas na segmentação de caracteres próximos e confusões visuais clássicas (ex: 'Z' vs '7', 'O' vs '0', 'E' vs 'F'), resultando em uma taxa de acerto de ~70% sem pós-processamento.

O PaddleOCR (PP-OCRv4) foi identificado como uma alternativa de estado da arte, com arquiteturas superiores (DBNet para detecção e SVTR para reconhecimento), mas apresentou desafios de compatibilidade de dependências nativas (MKL) no ambiente Python 3.13.

## Decisão
1. **Migração para PaddleOCR:** Substituir o EasyOCR pelo PaddleOCR (PP-OCRv4) como motor principal de leitura, resolvendo as dependências de ambiente (Intel MKL) para garantir a execução no Python 3.13.
2. **Camada de Correção Heurística (Minimum Edit Distance):** Implementar um módulo de pós-processamento que não apenas valida, mas *corrige* ativamente o output do OCR. O algoritmo testa o texto bruto contra as regras dos padrões Antigo e Mercosul, aplicando um dicionário de confusões visuais e escolhendo o padrão que exigir o "menor custo" (menor número de alterações) para se tornar válido.

## Consequências

### Positivas
- **Acurácia:** Acurácia de leitura subiu para 100% no conjunto de teste de imagens "selvagens" (internet), contra 70% do EasyOCR puro.
- **Robustez de Negócio:** O sistema não rejeita uma placa com um único erro de OCR (ex: ler '0' no lugar de 'O'). Ele corrige ativamente baseado nas regras do DETRAN.
- **Resiliência:** O parsing robusto do PaddleOCR lida nativamente com distorções de perspectiva que quebravam o CRAFT (EasyOCR).

### Negativas / Trade-offs
- **Complexidade de Ambiente:** O PaddleOCR exige um setup mais rigoroso de bibliotecas C++ (MKL) e não é trivial em versões muito recentes do Python (3.13+), exigindo manutenção de dependências.
- **Latência:** O PP-OCRv4 é computacionalmente mais pesado que o EasyOCR. Em um cenário de altíssima vazão, seria necessário avaliar o uso de GPUs dedicadas ou otimização via ONNX/TensorRT.
- **Over-engineering:** A camada de correção heurística adiciona complexidade ao código. Se o modelo de OCR fosse 100% perfeito (ex: um LPRNet fine-tuned com 500k imagens), essa camada seria redundante. No entanto, para um MVP sem fine-tuning massivo, ela é essencial.