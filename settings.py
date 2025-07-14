from pathlib import Path
import os
from sqlalchemy import create_engine

# Direktori utama proyek
FILE = Path(__file__).resolve()
ROOT = FILE.parent

# Path untuk model YOLO
MODEL_DIR = ROOT / 'weights'
DETECTION_MODEL_PATH = MODEL_DIR / 'model-deteksi-apd.pt'

# Path untuk aset
IMAGES_DIR = ROOT / 'assets'
DEFAULT_IMAGE = IMAGES_DIR / 'testing-apd-gundar5.jpg'
DEFAULT_DETECT_IMAGE = IMAGES_DIR / 'testing-apd-gundar5-detected.jpg'

# Konfigurasi database
DATABASE_NAME = "ppe_detection_history.db"
DATABASE_URL = f"sqlite:///{ROOT / DATABASE_NAME}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # check_same_thread untuk SQLite

# Opsi untuk sidebar
IMAGE = 'Gambar'
SOURCES_LIST = [IMAGE]