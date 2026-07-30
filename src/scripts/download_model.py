import gdown
import os

MODEL_ROOT = "./best.pt"
TARGET_DIR = "./models"
NEW_MODEL_PATH = os.path.join(TARGET_DIR, "best.pt")

if not os.path.exists(MODEL_ROOT) and not os.path.exists(NEW_MODEL_PATH):
    url = "https://drive.google.com/file/d/1PvGgaiwGeP0CMG_Ye4eXXMg1PhYu6HA1/view?usp=sharing"
    gdown.download(url)  # type: ignore

    if not os.path.exists(NEW_MODEL_PATH):
        os.makedirs(TARGET_DIR, exist_ok=True)

    os.rename(MODEL_ROOT, NEW_MODEL_PATH)

else:
    print("Model já baixado!")
