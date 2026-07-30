import re
from pathlib import Path

import cv2
import numpy as np
from paddleocr import PaddleOCR


class PlateOCR:
    """
    Pipeline de OCR para leitura de placas veiculares
    Inclui pré-processamento da imagem e validação via Regex.
    """

    def __init__(self, languages=["en"], gpu=False):
        """
        Metódo padrão que define o que deve ser definido ao iniciar
        um objeto da classe "PlateOCR"
        """
        print("🚀 Inicializando o Paddle OCR")
        self.ocr = PaddleOCR(
            lang="en",
            ocr_version="PP-OCRv4",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,
        )

        # Dicionário de ajustes em caso da leitura de placas enfrentar problemas
        self.confusions = {
            "Z": "2",
            "2": "Z",
            "7": "T",
            "T": "7",
            "E": "F",
            "F": "E",
            "O": "0",
            "0": "O",
            "Q": "0",
            "D": "0",
            "S": "5",
            "5": "S",
            "B": "8",
            "8": "B",
            "G": "6",
            "6": "G",
            "I": "1",
            "1": "I",
            "L": "1",
            "A": "4",
            "4": "A",
            "U": "V",
            "V": "U",
        }
        print("✅ PaddleOCR em funcionamento!")

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Aplicamos técnicas de pré-processamento para melhorar
        a capacidade de leitura do OCR, tornando imagens
        maiores e nítidas
        """

        target_height = 320
        current_height = image.shape[0]

        if current_height < target_height:
            scale = target_height / current_height
            print(
                f"O atual current_height é {current_height}\n e a scale recomendada é: {scale:.2f}"
            )
        else:
            scale = 1.0

        new_width = int(image.shape[1] * scale)
        new_height = int(image.shape[0] * scale)

        resized = cv2.resize(
            image, (new_width, new_height), interpolation=cv2.INTER_CUBIC
        )

        blur = cv2.GaussianBlur(resized, (0, 0), sigmaX=1.5)

        # Suavização leve mantendo os 3 canais de cor intactos
        processed = cv2.GaussianBlur(blur, (3, 3), 0)

        # Salvamos para fins de DEBUG
        cv2.imwrite(f"outputs/ocr_images/final_image.jpg", processed)

        return processed

    def read_plate(self, image: np.ndarray) -> dict:
        """
        Lê a placa usando a nova API .predict() do PaddleOCR com parsing robusto.
        """
        processed_img = self.preprocess_image(image)

        results = self.ocr.predict(processed_img)

        texts = []

        # O PaddleOCR retorna uma lista de detecções. Vamos extrair apenas os textos.
        texts = [res["rec_texts"][0] for res in results if res["rec_texts"]]

        if not texts:
            return {
                "raw_text": "",
                "corrected_text": "",
                "validated_plate": None,
                "ocr_details": [],
            }

        raw_text = texts[0]

        # Limpeza final via Regex (garante que só sobrou alfanumérico)
        raw_text = re.sub(r"[^A-Z0-9]", "", raw_text)

        corrected_text = self.correct_plate_by_pattern(raw_text)

        return {
            "raw_text": raw_text,
            "corrected_text": corrected_text,
            "validated_plate": self.validate_plate(corrected_text),
            "ocr_details": texts,  # Útil para debugar o que ele leu separadamente
        }

    def validate_plate(self, text: str) -> str | None:
        """
        Valida se o texto lido corresponde ao formato de placa Brasileiro.
        Retorna o texto formatado se válido, ou None se inválido
        """

        if len(text) != 7:
            return None

        # Padrão antigo: AAA-0000 (3 letras, 4 números)
        pattern_old = r"^[A-Z]{3}[0-9]{4}$"

        # Padrão Mercosul AAA0A00 (4 letras, 3 números)
        pattern_mercosul = r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$"

        if re.match(pattern_old, text):
            return f"{text[:3]}-{text[3:]}"
        elif re.match(pattern_mercosul, text):
            return text
        else:
            return None

    def correct_plate_by_pattern(self, text: str) -> str:
        """
        Corrige a placa usando a lógica de 'Menor Custo' (Minimum Edit Distance).
        O padrão que exigir menos trocas para ser válido é o escolhido.
        """
        if len(text) != 7:
            return text

        # Regras para cada padrão (índice: tipo esperado)
        rules_old = {
            0: "alpha",
            1: "alpha",
            2: "alpha",
            3: "digit",
            4: "digit",
            5: "digit",
            6: "digit",
        }
        rules_merc = {
            0: "alpha",
            1: "alpha",
            2: "alpha",
            3: "digit",
            4: "alpha",
            5: "digit",
            6: "digit",
        }

        # Tenta corrigir para ambos os padrões
        fix_old, cost_old = self._apply_corrections(text, rules_old)
        fix_merc, cost_merc = self._apply_corrections(text, rules_merc)

        # O Juiz Final (validate_plate)
        valid_old = self.validate_plate(fix_old) if fix_old else None
        valid_merc = self.validate_plate(fix_merc) if fix_merc else None

        # Lógica de decisão:
        # 1. Se apenas um for válido, retorna ele.
        if valid_old and not valid_merc:
            return valid_old
        if valid_merc and not valid_old:
            return valid_merc

        # 2. Se ambos forem válidos (ou nenhum), retorna o que teve MENOR custo (menos alterações)
        if cost_old <= cost_merc:
            return valid_old if valid_old else text
        else:
            return valid_merc if valid_merc else text

    def _apply_corrections(self, text: str, rules: dict) -> tuple[str | None, int]:
        """
        Tenta aplicar as regras. Retorna a string corrigida e o número de alterações feitas.
        Se for impossível corrigir, retorna None e custo 999.
        """
        chars = list(text)
        changes = 0

        for pos, expected_type in rules.items():
            char = chars[pos]

            # Violação: Esperava número, veio letra
            if expected_type == "digit" and char.isalpha():
                if char in self.confusions and self.confusions[char].isdigit():
                    chars[pos] = self.confusions[char]
                    changes += 1
                else:
                    return None, 999  # Impossível corrigir

            # Violação: Esperava letra, veio número
            elif expected_type == "alpha" and char.isdigit():
                if char in self.confusions and self.confusions[char].isalpha():
                    chars[pos] = self.confusions[char]
                    changes += 1
                else:
                    return None, 999  # Impossível corrigir

        return "".join(chars), changes


# Script para teste:
if __name__ == "__main__":
    # Teste rápido
    ocr = PlateOCR()

    # Carregar um dos seus recortes
    test_crop_path = "outputs/pipeline_debug/crop_1_IYJ7F537.jpg"  # Ajuste o caminho de uma imagem para testar
    test_crop = cv2.imread(test_crop_path)

    if test_crop is not None:
        result = ocr.read_plate(test_crop)
        print(result)
