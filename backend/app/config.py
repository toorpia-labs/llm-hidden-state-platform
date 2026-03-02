import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # project root
DATA_DIR = BASE_DIR / "data" / "jobs"
MODELS_CONFIG_PATH = BASE_DIR / "backend" / "models.yaml"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

CUDA_VISIBLE_DEVICES = os.getenv("CUDA_VISIBLE_DEVICES", "0")
HF_HOME = os.getenv("HF_HOME", None)
