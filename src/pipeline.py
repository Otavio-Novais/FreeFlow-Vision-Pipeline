import cv2
from pathlib import Path
from typing import Optional, List, Dict
from inference import VehicleDetector
from ocr_pipeline import PlateOCR
from database.repository import TransactionRepository

class FreeFlowPipeline:
    """
    Orquestrador principal do sistema Free Flow.
    Integra Visão Computacional (YOLO + PaddleOCR) com Regras de Negócio (Banco de Dados).
    """

    def __init__(self, db_path: str = "data/freeflow.db", conf_threshold: float = 0.2):
        print("🚀 Inicializando o Pipeline Free Flow...")
        
        # 1. Inicializa os componentes usando as classes reais
        self.detector = VehicleDetector(conf_threshold=conf_threshold)
        self.ocr = PlateOCR()
        self.db_repo = TransactionRepository() # Já inicializa schema e seed
        
        # Mapeamento de classes do YOLO para o Banco de Dados
        # O YOLO pode retornar 'car', 'truck', etc. O banco espera 'carro', 'caminhao_medio'.
        self.class_mapping = {
            'carro': 'carro',
            'car': 'carro',
            'moto': 'moto',
            'motorcycle': 'moto',
            'caminhao': 'caminhao_medio',
            'truck': 'caminhao_medio',
            'onibus': 'onibus',
            'bus': 'onibus'
        }
        print("✅ Pipeline pronto para processar imagens!")

    def process_image(
        self, 
        image_path: str, 
        gate_id: int = 1, 
        obo_tag: Optional[str] = None,
        save_debug: bool = True
    ) -> List[Dict]:
        """
        Processa uma imagem completa simulando a passagem no pórtico.
        """
        img_path = Path(image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

        print(f"\n📸 Processando imagem: {img_path.name} | Pórtico: {gate_id}")
        
        # 1. Detecção de Veículos (YOLO)
        # O método detect() retorna list[dict] com keys: class_id, class_name, confidence, bbox
        detections = self.detector.detect(image_path, save_results=save_debug)
        
        if not detections:
            print("⚠️ Nenhum veículo detectado na imagem.")
            return []

        transactions = []

        # 2. Itera sobre cada veículo detectado
        for i, det in enumerate(detections):
            print(f"\n--- Veículo {i+1} ---")
            print(f"  Tipo (YOLO): {det['class_name']} | Confiança: {det['confidence']:.2%}")
            
            # Normaliza a classe para o formato do Banco de Dados
            db_vehicle_type = self.class_mapping.get(det['class_name'].lower(), 'carro')
            
            # 3. Recorte do Veículo
            # crop_vehicle() recebe image_path (str) e bbox (list), retorna np.ndarray
            cropped_img = self.detector.crop_vehicle(image_path, det['bbox'])
            
            if cropped_img is None or cropped_img.size == 0:
                print("  ❌ Erro ao recortar a imagem do veículo.")
                continue

            # 4. Leitura da Placa (PaddleOCR)
            # read_plate() recebe np.ndarray e retorna dict com raw_text, corrected_text, validated_plate
            ocr_result = self.ocr.read_plate(cropped_img)
            
            print(f"  🔍 OCR Bruto: {ocr_result['raw_text']}")
            print(f"  🛠️ OCR Corrigido: {ocr_result['corrected_text']}")
            print(f"  ✅ Placa Válida: {ocr_result['validated_plate']}")

            # 5. Registro no Banco de Dados (Apenas se a placa for válida)
            if ocr_result['validated_plate']:
                transaction = self.db_repo.register_transaction(
                    gate_id=gate_id,
                    plate_read=ocr_result['validated_plate'],
                    vehicle_detected=db_vehicle_type,
                    plate_confidence=0.95, # Em produção, viria do OCR
                    vehicle_confidence=det['confidence'],
                    obo_tag_number=obo_tag
                )
                
                transactions.append(transaction)
                
                print(f"  💾 Transação registrada no DB!")
                print(f"     ID: {transaction['transaction_id']} | Status: {transaction['status']}")
                print(f"     Valor: R$ {transaction['toll_amount']:.2f}")
                
                if transaction['divergence_reason']:
                    print(f"     ⚠️ Divergência: {transaction['divergence_reason']}")
            else:
                print("  ⚠️ Placa não pôde ser validada. Transação ignorada.")

            # (Opcional) Salvar o recorte para debug
            if save_debug:
                debug_dir = Path("outputs/pipeline_debug")
                debug_dir.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(
                    str(debug_dir / f"crop_{i}_{ocr_result['raw_text']}.jpg"), 
                    cropped_img
                )

        return transactions

    def get_audit_report(self):
        """Retorna um resumo das divergências para auditoria."""
        divergences = self.db_repo.get_divergences()
        print(f"\n Relatório de Auditoria ({len(divergences)} divergências):")
        for div in divergences:
            print(f"  - {div['plate_read']} ({div['status']}) | {div['divergence_reason']}")
        return divergences

    def close(self):
        """Encerra as conexões."""
        self.db_repo.close()
        print("\n🔒 Pipeline encerrado.")


# ==========================================
# Script de Execução Direta (Teste de Integração)
# ==========================================
if __name__ == '__main__':
    # Inicializa o pipeline
    pipeline = FreeFlowPipeline()

    # Caminho para uma imagem de teste (Ajuste para o seu ambiente)
    test_image = "test_images/brasil_placa1.jpg" 
    
    # Cenário 1: Passagem Normal (Tag correta para a placa)
    print("="*50)
    print("CENÁRIO 1: Passagem Normal (Tag OBO-002)")
    print("="*50)
    try:
        pipeline.process_image(test_image, gate_id=1, obo_tag='OBO-002')
    except FileNotFoundError:
        print(f"⚠️ Imagem de teste '{test_image}' não encontrada.")

    # Cenário 2: Passagem com Divergência (Tag de outro carro)
    print("\n" + "="*50)
    print("CENÁRIO 2: Divergência (Tag OBO-001 - de outro carro)")
    print("="*50)
    try:
        pipeline.process_image(test_image, gate_id=1, obo_tag='OBO-001')
    except FileNotFoundError:
        pass

    # Cenário 3: Sem Tag (Fluxo de notificação)
    print("\n" + "="*50)
    print("CENÁRIO 3: Sem Tag (UNREGISTERED)")
    print("="*50)
    try:
        pipeline.process_image(test_image, gate_id=2, obo_tag=None)
    except FileNotFoundError:
        pass

    # Gera o relatório final
    pipeline.get_audit_report()
    
    # Limpeza
    pipeline.close()