"""Verify that PaddleOCR is installed successfully."""

from importlib import import_module

try:
    paddleocr = import_module("paddleocr")
except ImportError:
    paddleocr = None

if paddleocr is not None:
    print(f"PaddleOCR version: {paddleocr.__version__}")
else:
    print("PaddleOCR is not installed.")

# If you use the local paddle_static inference engine, you can further verify PaddlePaddle and GPU availability
try:
    paddle = import_module("paddle")
except ImportError:
    paddle = None

if paddle is not None:
    print(f"Paddle version: {paddle.__version__}")
    print(f"GPU available: {paddle.is_compiled_with_cuda()}")
    print(f"GPU count: {paddle.device.cuda.device_count()}")
else:
    print("Paddle is not installed.")
