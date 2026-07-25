from ultralytics import YOLO
from config import MODEL_WEIGHTS_PATH

model = YOLO(MODEL_WEIGHTS_PATH)

print("Importado!")