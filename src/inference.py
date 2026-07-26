from ultralytics import YOLO
from pathlib import Path
import cv2
import numpy as np
from config import MODEL_WEIGHTS_PATH, IMG_TEST_DIR, OUTPUTS_DIR  # type: ignore

class VehicleDetector:
    """
    Classe para detectar veículos e preparar imagens para OCR
    """

    def __init__(self, weights_path: str = MODEL_WEIGHTS_PATH, conf_threshold: float = 0.05):
        """
        Inicializa os pesos do modelo.

        Args:
            weights_path: Caminho para o arquivo .pt
            conf_threshold: Threshold de confiança (0.0 a 1.0)
        """

        self.model = YOLO(weights_path)
        self.conf_threshold = conf_threshold

    def detect(self, image_path: str, save_results:bool = False) -> list[dict]:
        """
        Detecta veículos na imagem e retorna as detecções

        Args:
            image_path: Caminho para a imagem
            save_results: se True, salva a imagem anotada

        Returns:
            Lista de dicionários com as declarações
        """
        results = self.model.predict(
            source= image_path,
            conf=self.conf_threshold,
            iou = 0.30,
            save = save_results,
            project=str(OUTPUTS_DIR),
            name='predictions',
            exist_ok=True,
            verbose=False
        )

        detections = []

        for result in results:
            if result.boxes is not None:
                boxes = result.boxes
                classes = boxes.cls.cpu().numpy().astype(int)
                confidences = boxes.conf.cpu().numpy()
                xyxy = boxes.xyxy.cpu().numpy()

                for i in range(len(boxes)):
                    detection = {
                        'class_id': classes[i],
                        'class_name': self.model.names[classes[i]],
                        'confidence': float(confidences[i]),
                        'bbox': xyxy[i].tolist() # [x1,y1,x2,y2]
                    }
                    detections.append(detection)

        return detections

    def crop_vehicle(self,  image_path: str, bbox: list) -> np.ndarray:
        """
        Recorta a região do veículo baseado na bounding box.

        Args:
            image_path: Caminho da Imagem
            bbox: Lista [x1,y1,x2,y2]
        """

        img = cv2.imread(image_path)
        x1,y1,x2,y2 = map(int,bbox)

        h,w = img.shape[:2]
        x1 = max(0, min(x1,w))
        y1 = max(0, min(y1,h))
        x2 = max(0, min(x2,w))
        y2 = max(0, min(y2,h))

        cropped = img[y1:y2, x1:x2]
        return cropped




if __name__ == '__main__':
    # 1. Criar detector com threshold mais alto para produção
    detector = VehicleDetector(conf_threshold=0.05)
    
    # 2. Pegar a primeira imagem de teste disponível
    test_image = str(list(Path(IMG_TEST_DIR).glob('*.jpg'))[0])
    print(f"🔍 Analisando: {test_image}")
    
    # 3. Rodar a detecção (save_results=False aqui para não duplicar com o YOLO, ou True se quiser)
    detections = detector.detect(test_image, save_results=True)
    
    print(f"\n🚗 {len(detections)} veículo(s) detectado(s):")
    
    # 4. Garantir que a pasta de recortes existe
    cropped_dir = Path(OUTPUTS_DIR) / 'cropped_vehicles'
    cropped_dir.mkdir(parents=True, exist_ok=True)
    
    for i, det in enumerate(detections):
        print(f"  {i+1}. {det['class_name'].upper()} - Confiança: {det['confidence']:.2%}")
        
        # 5. Recortar o veículo e salvar usando o caminho correto
        cropped = detector.crop_vehicle(test_image, det['bbox'])
        
        # Salvar na pasta correta que acabamos de criar
        save_path = cropped_dir / f'cropped_{det["class_name"]}_{i}.jpg'
        cv2.imwrite(str(save_path), cropped)
        print(f"     ✅ Recorte salvo em: {save_path}")