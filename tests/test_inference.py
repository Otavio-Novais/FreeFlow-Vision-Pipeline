import unittest

import cv2
import numpy as np

from inference import VehicleDetector


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
