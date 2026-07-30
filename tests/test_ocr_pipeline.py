import unittest
from unittest.mock import patch

import numpy as np

from ocr_pipeline import PlateOCR


def _make_ocr_instance():
    with patch("ocr_pipeline.PaddleOCR"):
        return PlateOCR()


class TestPlateOCRInit(unittest.TestCase):
    def test_paddleocr_called_with_default_params(self):
        with patch("ocr_pipeline.PaddleOCR") as mock_paddle:
            PlateOCR()
            mock_paddle.assert_called_once()
            call_kwargs = mock_paddle.call_args.kwargs
            self.assertEqual(call_kwargs["lang"], "en")
            self.assertEqual(call_kwargs["ocr_version"], "PP-OCRv4")
            self.assertEqual(call_kwargs["use_doc_orientation_classify"], False)
            self.assertEqual(call_kwargs["use_doc_unwarping"], False)
            self.assertEqual(call_kwargs["use_textline_orientation"], False)

    def test_confusions_dict_populated(self):
        with patch("ocr_pipeline.PaddleOCR"):
            ocr = PlateOCR()
        self.assertIsInstance(ocr.confusions, dict)
        self.assertGreater(len(ocr.confusions), 10)
        self.assertIn("Z", ocr.confusions)
        self.assertIn("2", ocr.confusions)
        self.assertIn("O", ocr.confusions)
        self.assertIn("0", ocr.confusions)

    def test_gpu_flag_passed(self):
        with patch("ocr_pipeline.PaddleOCR") as mock_paddle:
            PlateOCR(gpu=True)
            mock_paddle.assert_called_once()
        with patch("ocr_pipeline.PaddleOCR") as mock_paddle:
            PlateOCR(gpu=False)
            mock_paddle.assert_called_once()


class TestPlateOCRReadPlate(unittest.TestCase):
    def setUp(self):
        patcher = patch("ocr_pipeline.PaddleOCR")
        self.mock_paddle = patcher.start()
        self.addCleanup(patcher.stop)
        self.ocr = PlateOCR()

    def test_empty_ocr_results(self):
        self.ocr.ocr.predict.return_value = [{"rec_texts": []}]
        with patch.object(
            self.ocr,
            "preprocess_image",
            return_value=np.zeros((300, 200, 3), dtype=np.uint8),
        ):
            result = self.ocr.read_plate(np.zeros((100, 200, 3), dtype=np.uint8))
        self.assertEqual(result["raw_text"], "")
        self.assertEqual(result["corrected_text"], "")
        self.assertIsNone(result["validated_plate"])

    def test_single_valid_text(self):
        self.ocr.ocr.predict.return_value = [{"rec_texts": ["IYJ7F53"]}]
        with patch.object(
            self.ocr,
            "preprocess_image",
            return_value=np.zeros((300, 200, 3), dtype=np.uint8),
        ):
            result = self.ocr.read_plate(np.zeros((100, 200, 3), dtype=np.uint8))
        self.assertEqual(result["raw_text"], "IYJ7F53")
        self.assertEqual(result["validated_plate"], "IYJ7F53")

    def test_multiple_texts_uses_first(self):
        self.ocr.ocr.predict.return_value = [{"rec_texts": ["ABC1234", "EXTRA567"]}]
        with patch.object(
            self.ocr,
            "preprocess_image",
            return_value=np.zeros((300, 200, 3), dtype=np.uint8),
        ):
            result = self.ocr.read_plate(np.zeros((100, 200, 3), dtype=np.uint8))
        self.assertEqual(result["raw_text"], "ABC1234")

    def test_non_alphanumeric_stripped(self):
        self.ocr.ocr.predict.return_value = [{"rec_texts": ["ABC-1234"]}]
        with patch.object(
            self.ocr,
            "preprocess_image",
            return_value=np.zeros((300, 200, 3), dtype=np.uint8),
        ):
            result = self.ocr.read_plate(np.zeros((100, 200, 3), dtype=np.uint8))
        self.assertEqual(result["raw_text"], "ABC1234")

    def test_invalid_plate_not_registered(self):
        self.ocr.ocr.predict.return_value = [{"rec_texts": ["XXXXXXX"]}]
        with patch.object(
            self.ocr,
            "preprocess_image",
            return_value=np.zeros((300, 200, 3), dtype=np.uint8),
        ):
            result = self.ocr.read_plate(np.zeros((100, 200, 3), dtype=np.uint8))
        self.assertIsNone(result["validated_plate"])


class TestValidatePlate(unittest.TestCase):
    def setUp(self):
        self.ocr = _make_ocr_instance()

    def test_old_format_valid(self):
        self.assertEqual(self.ocr.validate_plate("ABC1234"), "ABC-1234")

    def test_mercosul_format_valid(self):
        self.assertEqual(self.ocr.validate_plate("IYJ7F53"), "IYJ7F53")

    def test_another_mercosul(self):
        self.assertEqual(self.ocr.validate_plate("AOX5G10"), "AOX5G10")

    def test_length_less_than_7(self):
        self.assertIsNone(self.ocr.validate_plate("ABC123"))

    def test_length_greater_than_7(self):
        self.assertIsNone(self.ocr.validate_plate("ABC12345"))

    def test_empty_string(self):
        self.assertIsNone(self.ocr.validate_plate(""))

    def test_all_numbers(self):
        self.assertIsNone(self.ocr.validate_plate("1234567"))

    def test_all_letters(self):
        self.assertIsNone(self.ocr.validate_plate("ABCDEFG"))

    def test_lowercase(self):
        self.assertIsNone(self.ocr.validate_plate("abc1234"))

    def test_wrong_mercosul_pattern(self):
        self.assertIsNone(self.ocr.validate_plate("AB1C234"))

    def test_with_special_chars(self):
        self.assertIsNone(self.ocr.validate_plate("ABC.1234"))

    def test_none_input(self):
        with self.assertRaises(TypeError):
            self.ocr.validate_plate(None)


class TestApplyCorrections(unittest.TestCase):
    def setUp(self):
        self.ocr = _make_ocr_instance()

    def test_all_matching_old_rules(self):
        result, cost = self.ocr._apply_corrections(
            "ABC1234",
            {
                0: "alpha",
                1: "alpha",
                2: "alpha",
                3: "digit",
                4: "digit",
                5: "digit",
                6: "digit",
            },
        )
        self.assertEqual(result, "ABC1234")
        self.assertEqual(cost, 0)

    def test_all_matching_mercosul_rules(self):
        result, cost = self.ocr._apply_corrections(
            "IYJ7F53",
            {
                0: "alpha",
                1: "alpha",
                2: "alpha",
                3: "digit",
                4: "alpha",
                5: "digit",
                6: "digit",
            },
        )
        self.assertEqual(result, "IYJ7F53")
        self.assertEqual(cost, 0)

    def test_digit_in_alpha_with_valid_confusion(self):
        result, cost = self.ocr._apply_corrections(
            "0BC1234",
            {
                0: "alpha",
                1: "alpha",
                2: "alpha",
                3: "digit",
                4: "digit",
                5: "digit",
                6: "digit",
            },
        )
        self.assertEqual(result, "OBC1234")
        self.assertEqual(cost, 1)

    def test_alpha_in_digit_with_valid_confusion(self):
        result, cost = self.ocr._apply_corrections(
            "ABC1Z34",
            {
                0: "alpha",
                1: "alpha",
                2: "alpha",
                3: "digit",
                4: "digit",
                5: "digit",
                6: "digit",
            },
        )
        self.assertEqual(result, "ABC1234")
        self.assertEqual(cost, 1)

    def test_digit_in_alpha_no_confusion_available(self):
        result, cost = self.ocr._apply_corrections(
            "3BC1234",
            {
                0: "alpha",
                1: "alpha",
                2: "alpha",
                3: "digit",
                4: "digit",
                5: "digit",
                6: "digit",
            },
        )
        self.assertIsNone(result)
        self.assertEqual(cost, 999)

    def test_alpha_in_digit_no_confusion_available(self):
        result, cost = self.ocr._apply_corrections(
            "ABC1J34",
            {
                0: "alpha",
                1: "alpha",
                2: "alpha",
                3: "digit",
                4: "digit",
                5: "digit",
                6: "digit",
            },
        )
        self.assertIsNone(result)
        self.assertEqual(cost, 999)

    def test_multiple_fixable_violations(self):
        result, cost = self.ocr._apply_corrections(
            "0BC1Z34",
            {
                0: "alpha",
                1: "alpha",
                2: "alpha",
                3: "digit",
                4: "digit",
                5: "digit",
                6: "digit",
            },
        )
        self.assertEqual(result, "OBC1234")
        self.assertEqual(cost, 2)

    def test_mixed_fixable_and_unfixable(self):
        result, cost = self.ocr._apply_corrections(
            "3BC1Z34",
            {
                0: "alpha",
                1: "alpha",
                2: "alpha",
                3: "digit",
                4: "digit",
                5: "digit",
                6: "digit",
            },
        )
        self.assertIsNone(result)
        self.assertEqual(cost, 999)

    def test_mercosul_pattern_alpha_in_digit_position(self):
        result, cost = self.ocr._apply_corrections(
            "IYJ7FS3",
            {
                0: "alpha",
                1: "alpha",
                2: "alpha",
                3: "digit",
                4: "alpha",
                5: "digit",
                6: "digit",
            },
        )
        self.assertEqual(result, "IYJ7F53")
        self.assertEqual(cost, 1)


class TestCorrectPlateByPattern(unittest.TestCase):
    def setUp(self):
        self.ocr = _make_ocr_instance()

    def test_perfect_old_format(self):
        result = self.ocr.correct_plate_by_pattern("ABC1234")
        self.assertIn(result, ("ABC-1234", "ABC1234"))

    def test_perfect_mercosul(self):
        result = self.ocr.correct_plate_by_pattern("IYJ7F53")
        self.assertIsNotNone(result)
        self.assertIn(result, ("IYJ7F53", "IYJ-7F53"))

    def test_wrong_length_returns_unchanged(self):
        result = self.ocr.correct_plate_by_pattern("ABC123")
        self.assertEqual(result, "ABC123")

    def test_one_correction_old_pattern(self):
        result = self.ocr.correct_plate_by_pattern("0BC1234")
        self.assertEqual(result, "OBC-1234")

    def test_one_correction_mercosul_pattern(self):
        result = self.ocr.correct_plate_by_pattern("ABC1D2O")
        self.assertIsNotNone(result)

    def test_both_patterns_valid_chooses_lower_cost(self):
        result = self.ocr.correct_plate_by_pattern("ABC1234")
        self.assertIsNotNone(result)
        self.assertIn(result, ("ABC-1234", "ABC1234"))

    def test_uncorrectable_returns_original(self):
        result = self.ocr.correct_plate_by_pattern("WXYPQRS")
        self.assertEqual(result, "WXYPQRS")


class TestPreprocessImage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("ocr_pipeline.PaddleOCR"):
            cls.ocr = PlateOCR()

    def test_small_image_upscaled(self):
        img = np.zeros((50, 80, 3), dtype=np.uint8)
        with patch("cv2.imwrite"):
            result = self.ocr.preprocess_image(img)
        self.assertGreaterEqual(result.shape[0], 300)

    def test_tall_image_not_resized(self):
        img = np.zeros((400, 200, 3), dtype=np.uint8)
        with patch("cv2.imwrite"):
            result = self.ocr.preprocess_image(img)
        self.assertEqual(result.shape[0], 400)

    def test_output_same_channels(self):
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        with patch("cv2.imwrite"):
            result = self.ocr.preprocess_image(img)
        self.assertEqual(result.shape[2], 3)

    def test_output_dimensions_aspect_ratio_preserved(self):
        img = np.zeros((50, 80, 3), dtype=np.uint8)
        with patch("cv2.imwrite"):
            result = self.ocr.preprocess_image(img)
        expected_width = int(80 * (320 / 50))
        self.assertEqual(result.shape[1], expected_width)
        self.assertEqual(result.shape[0], 320)

    def test_image_changed_after_sharpening(self):
        np.random.seed(42)
        img = np.random.randint(0, 256, (100, 200, 3), dtype=np.uint8)
        with patch("cv2.imwrite"):
            result = self.ocr.preprocess_image(img)
        self.assertFalse(np.array_equal(img, result[:100, :200]))

    def test_grayscale_image_handled(self):
        img = np.zeros((100, 200), dtype=np.uint8)
        with patch("cv2.imwrite"):
            result = self.ocr.preprocess_image(img)
        self.assertGreater(result.shape[0], 0)
        self.assertGreater(result.shape[1], 0)


if __name__ == "__main__":
    unittest.main()
