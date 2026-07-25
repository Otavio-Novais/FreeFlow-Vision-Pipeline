import os
from roboflow import Roboflow

roboflowApiKey = os.environ.get('roboflowApi')
DATASET_ROOT = './placas_brasileiras-10'
TARGET_DIR = "./datasets"
NEW_DATASET_PATH = os.path.join(TARGET_DIR,"placas_brasileiras_10")


if not os.path.exists(DATASET_ROOT):
  rf = Roboflow(api_key=roboflowApiKey)
  project = rf.workspace("alfascan").project("placas_brasileiras")
  version = project.version(10)
  dataset = version.download("yolov8")
  # Usamos a API da RoboFlow para baixar o dataset disponibilizado por eles
  # Baixamos a versão YoLoV8, apesar do arquivo .txt não estar padronizado;

  if not os.path.exists(NEW_DATASET_PATH):
    os.makedirs(TARGET_DIR,exist_ok=True)

  os.rename(DATASET_ROOT,NEW_DATASET_PATH)

else:
  print('Dataset já baixado!')

