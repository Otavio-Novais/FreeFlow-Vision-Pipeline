import unittest
from unittest.mock import MagicMock, patch

import cv2
import numpy as np

from config import MODEL_WEIGHTS_PATH
from inference import VehicleDetector


class TestVehicleDetectorInit(unittest.TestCase):
    def test_default_weights_path(self):
        with patch("inference.YOLO") as mock_yolo:
            VehicleDetector()
            mock_yolo.assert_called_once()
            arg = mock_yolo.call_args.args[0]
            self.assertEqual(str(arg), str(MODEL_WEIGHTS_PATH))

    def test_custom_conf_threshold(self):
        with patch("inference.YOLO"):
            detector = VehicleDetector(conf_threshold=0.75)
            self.assertEqual(detector.conf_threshold, 0.75)

    def test_default_conf_threshold(self):
        with patch("inference.YOLO"):
            detector = VehicleDetector()
            self.assertEqual(detector.conf_threshold, 0.05)


class TestVehicleDetectorDetect(unittest.TestCase):
    def setUp(self):
        patcher = patch("inference.YOLO")
        self.mock_yolo_cls = patcher.start()
        self.addCleanup(patcher.stop)
        self.detector = VehicleDetector(conf_threshold=0.2)
        self.detector.model.names = {0: "carro", 1: "moto"}

    def _make_result(self, cls_data, conf_data, xyxy_data):
        result = MagicMock()
        result.boxes = MagicMock()
        result.boxes.__len__.return_value = len(cls_data)
        result.boxes.cls.cpu.return_value.numpy.return_value.astype.return_value = (
            np.array(cls_data)
        )
        result.boxes.conf.cpu.return_value.numpy.return_value = np.array(
            conf_data, dtype=np.float32
        )
        result.boxes.xyxy.cpu.return_value.numpy.return_value = np.array(
            xyxy_data, dtype=np.float32
        )
        return result

    def test_no_detections(self):
        empty_result = MagicMock()
        empty_result.boxes = None
        self.detector.model.predict.return_value = [empty_result]

        detections = self.detector.detect("/tmp/fake.jpg")
        self.assertEqual(detections, [])

    def test_single_detection(self):
        result = self._make_result(
            cls_data=[0],
            conf_data=[0.95],
            xyxy_data=[[10.0, 20.0, 100.0, 200.0]],
        )
        self.detector.model.predict.return_value = [result]

        detections = self.detector.detect("/tmp/fake.jpg")
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]["class_id"], 0)
        self.assertEqual(detections[0]["class_name"], "carro")
        self.assertAlmostEqual(detections[0]["confidence"], 0.95)
        self.assertEqual(detections[0]["bbox"], [10.0, 20.0, 100.0, 200.0])

    def test_multiple_detections(self):
        result = self._make_result(
            cls_data=[0, 1, 0],
            conf_data=[0.90, 0.85, 0.70],
            xyxy_data=[
                [10, 20, 100, 200],
                [30, 40, 120, 180],
                [50, 60, 140, 160],
            ],
        )
        self.detector.model.predict.return_value = [result]

        detections = self.detector.detect("/tmp/fake.jpg")
        self.assertEqual(len(detections), 3)
        self.assertEqual(detections[0]["class_name"], "carro")
        self.assertEqual(detections[1]["class_name"], "moto")
        self.assertEqual(detections[2]["class_name"], "carro")

    def test_save_results_true(self):
        result = self._make_result(
            cls_data=[0],
            conf_data=[0.95],
            xyxy_data=[[10, 20, 100, 200]],
        )
        self.detector.model.predict.return_value = [result]

        self.detector.detect("/tmp/fake.jpg", save_results=True)
        self.detector.model.predict.assert_called_once()
        call_kwargs = self.detector.model.predict.call_args.kwargs
        self.assertTrue(call_kwargs["save"])

    def test_predict_called_with_correct_params(self):
        result = self._make_result(cls_data=[], conf_data=[], xyxy_data=[])
        self.detector.model.predict.return_value = [result]

        self.detector.detect("/tmp/fake.jpg", save_results=False)
        call_kwargs = self.detector.model.predict.call_args.kwargs
        self.assertEqual(call_kwargs["source"], "/tmp/fake.jpg")
        self.assertEqual(call_kwargs["conf"], 0.2)
        self.assertEqual(call_kwargs["iou"], 0.50)
        self.assertEqual(call_kwargs["save"], False)
        self.assertEqual(call_kwargs["verbose"], False)


class TestCropVehicle(unittest.TestCase):
    @classmethod
    def setUpClassClass(cls):
        pass

    def setUp(self):
        self.img_path = "/tmp/test_crop_image.jpg"
        self.img = np.zeros((100, 200, 3), dtype=np.uint8)
        self.img[30:70, 50:150] = [255, 255, 255]
        cv2.imwrite(self.img_path, self.img)

    def test_normal_bbox_within_bounds(self):
        detector = VehicleDetector.__new__(VehicleDetector)
        cropped = detector.crop_vehicle(self.img_path, [50, 30, 150, 70])
        self.assertEqual(cropped.shape, (40, 100, 3))

    def test_x1_below_zero_clamped(self):
        detector = VehicleDetector.__new__(VehicleDetector)
        cropped = detector.crop_vehicle(self.img_path, [-20, 30, 150, 70])
        self.assertEqual(cropped[0, 0, 0], self.img[30, 0, 0])

    def test_y1_below_zero_clamped(self):
        detector = VehicleDetector.__new__(VehicleDetector)
        cropped = detector.crop_vehicle(self.img_path, [50, -10, 150, 70])
        self.assertEqual(cropped[0, 0, 0], self.img[0, 50, 0])

    def test_x2_above_width_clamped(self):
        detector = VehicleDetector.__new__(VehicleDetector)
        cropped = detector.crop_vehicle(self.img_path, [50, 30, 300, 70])
        self.assertEqual(cropped.shape[1], 150)

    def test_y2_above_height_clamped(self):
        detector = VehicleDetector.__new__(VehicleDetector)
        cropped = detector.crop_vehicle(self.img_path, [50, 30, 150, 200])
        self.assertEqual(cropped.shape[0], 70)

    def test_bbox_completely_outside(self):
        detector = VehicleDetector.__new__(VehicleDetector)
        cropped = detector.crop_vehicle(self.img_path, [300, 300, 400, 400])
        self.assertEqual(cropped.size, 0)

    def test_float_bbox_cast_to_int(self):
        detector = VehicleDetector.__new__(VehicleDetector)
        cropped = detector.crop_vehicle(self.img_path, [50.7, 30.2, 150.9, 70.4])
        self.assertEqual(cropped.shape, (40, 100, 3))

    def test_zero_area_bbox(self):
        detector = VehicleDetector.__new__(VehicleDetector)
        cropped = detector.crop_vehicle(self.img_path, [50, 30, 50, 30])
        self.assertEqual(cropped.size, 0)


if __name__ == "__main__":
    unittest.main()
