from pathlib import Path

# Pega o diretório raiz do projeto (sobe dois níveis a partir de src/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Caminhos do Dataset
DATASET_DIR = BASE_DIR / "datasets" / "placas_brasileiras-10"
DATA_YAML_PATH = DATASET_DIR / "data.yaml"

# Caminhos do Modelo
MODELS_DIR = BASE_DIR / "models"
MODEL_WEIGHTS_PATH = MODELS_DIR / "best.pt"  # O peso que você vai baixar/colocar aqui

# Caminhos de Output
OUTPUTS_DIR = BASE_DIR / "outputs"

# Caminho das imagens testes
IMG_TEST_DIR = BASE_DIR / "test_images"
