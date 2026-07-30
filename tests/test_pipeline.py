import unittest
from unittest.mock import MagicMock, patch

from pipeline import FreeFlowPipeline


class TestFreeFlowPipelineInit(unittest.TestCase):
    @patch("pipeline.TransactionRepository")
    @patch("pipeline.PlateOCR")
    @patch("pipeline.VehicleDetector")
    def test_components_initialized(self, mock_detector, mock_ocr, mock_repo):
        pipeline = FreeFlowPipeline()
        mock_detector.assert_called_once_with(conf_threshold=0.15)
        mock_ocr.assert_called_once()
        mock_repo.assert_called_once()

    @patch("pipeline.TransactionRepository")
    @patch("pipeline.PlateOCR")
    @patch("pipeline.VehicleDetector")
    def test_custom_conf_threshold(self, mock_detector, mock_ocr, mock_repo):
        pipeline = FreeFlowPipeline(conf_threshold=0.5)
        mock_detector.assert_called_once_with(conf_threshold=0.5)

    @patch("pipeline.TransactionRepository")
    @patch("pipeline.PlateOCR")
    @patch("pipeline.VehicleDetector")
    def test_class_mapping_contains_expected_keys(
        self, mock_detector, mock_ocr, mock_repo
    ):
        pipeline = FreeFlowPipeline()
        self.assertIn("carro", pipeline.class_mapping)
        self.assertIn("car", pipeline.class_mapping)
        self.assertIn("moto", pipeline.class_mapping)
        self.assertIn("motorcycle", pipeline.class_mapping)
        self.assertIn("caminhao", pipeline.class_mapping)
        self.assertIn("truck", pipeline.class_mapping)

    @patch("pipeline.TransactionRepository")
    @patch("pipeline.PlateOCR")
    @patch("pipeline.VehicleDetector")
    def test_class_mapping_maps_correctly(self, mock_detector, mock_ocr, mock_repo):
        pipeline = FreeFlowPipeline()
        self.assertEqual(pipeline.class_mapping["carro"], "carro")
        self.assertEqual(pipeline.class_mapping["car"], "carro")
        self.assertEqual(pipeline.class_mapping["moto"], "moto")
        self.assertEqual(pipeline.class_mapping["motorcycle"], "moto")
        self.assertEqual(pipeline.class_mapping["caminhao"], "caminhao_medio")
        self.assertEqual(pipeline.class_mapping["truck"], "caminhao_medio")


class TestFreeFlowPipelineMethods(unittest.TestCase):
    def setUp(self):
        patcher_det = patch("pipeline.VehicleDetector")
        patcher_ocr = patch("pipeline.PlateOCR")
        patcher_repo = patch("pipeline.TransactionRepository")
        self.mock_detector = patcher_det.start()
        self.mock_ocr = patcher_ocr.start()
        self.mock_repo = patcher_repo.start()
        self.addCleanup(patcher_det.stop)
        self.addCleanup(patcher_ocr.stop)
        self.addCleanup(patcher_repo.stop)
        self.pipeline = FreeFlowPipeline()

    def test_get_audit_report_with_divergences(self):
        mock_divergences = [
            {
                "plate_read": "XYZ9999",
                "status": "DIVERGENCE",
                "divergence_reason": "...",
            },
            {
                "plate_read": "GHI5678",
                "status": "UNREGISTERED",
                "divergence_reason": "...",
            },
        ]
        self.pipeline.db_repo.get_divergences.return_value = mock_divergences

        result = self.pipeline.get_audit_report()
        self.assertEqual(result, mock_divergences)
        self.pipeline.db_repo.get_divergences.assert_called_once()

    def test_get_audit_report_empty(self):
        self.pipeline.db_repo.get_divergences.return_value = []

        result = self.pipeline.get_audit_report()
        self.assertEqual(result, [])

    def test_close_delegates_to_repo(self):
        self.pipeline.close()
        self.pipeline.db_repo.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
