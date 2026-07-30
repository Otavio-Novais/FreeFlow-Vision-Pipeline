import unittest
from pathlib import Path

from config import (
    BASE_DIR,
    DATA_YAML_PATH,
    DATASET_DIR,
    IMG_TEST_DIR,
    MODEL_WEIGHTS_PATH,
    MODELS_DIR,
    OUTPUTS_DIR,
)


class TestConfig(unittest.TestCase):
    def test_base_dir_is_project_root(self):
        readme = BASE_DIR / "README.md"
        src_dir = BASE_DIR / "src"
        self.assertTrue(readme.exists(), f"README.md not found at {readme}")
        self.assertTrue(src_dir.is_dir(), f"src/ not found at {src_dir}")

    def test_all_paths_are_absolute(self):
        paths = [
            BASE_DIR,
            DATASET_DIR,
            DATA_YAML_PATH,
            MODELS_DIR,
            MODEL_WEIGHTS_PATH,
            OUTPUTS_DIR,
            IMG_TEST_DIR,
        ]
        for p in paths:
            self.assertTrue(p.is_absolute(), f"{p} is not absolute")

    def test_all_paths_are_path_objects(self):
        paths = [
            BASE_DIR,
            DATASET_DIR,
            DATA_YAML_PATH,
            MODELS_DIR,
            MODEL_WEIGHTS_PATH,
            OUTPUTS_DIR,
            IMG_TEST_DIR,
        ]
        for p in paths:
            self.assertIsInstance(p, Path, f"{p} is not a Path object")

    def test_models_dir_exists(self):
        self.assertTrue(MODELS_DIR.is_dir())

    def test_model_weights_exists(self):
        self.assertTrue(MODEL_WEIGHTS_PATH.exists())

    def test_outputs_dir_exists(self):
        self.assertTrue(OUTPUTS_DIR.is_dir())

    def test_test_images_dir_exists(self):
        self.assertTrue(IMG_TEST_DIR.is_dir())

    def test_data_yaml_points_to_correct_dataset(self):
        self.assertIn("placas_brasileiras-10", str(DATA_YAML_PATH))

    def test_dataset_dir_name_matches_data_yaml_parent(self):
        self.assertEqual(DATASET_DIR, DATA_YAML_PATH.parent)


if __name__ == "__main__":
    unittest.main()
