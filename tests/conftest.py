import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture
def synthetic_image():
    return np.zeros((100, 200, 3), dtype=np.uint8)


@pytest.fixture
def synthetic_small_image():
    return np.zeros((50, 80, 3), dtype=np.uint8)


@pytest.fixture
def synthetic_tall_image():
    return np.zeros((400, 200, 3), dtype=np.uint8)


@pytest.fixture
def temp_image_file(tmp_path, synthetic_image):
    import cv2

    path = tmp_path / "test_image.jpg"
    cv2.imwrite(str(path), synthetic_image)
    return str(path)
