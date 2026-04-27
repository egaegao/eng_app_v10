from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
OUTPUT_DIR = BASE_DIR / "output"

DEFAULT_FILE_NAME = "dummy_mining_production.xlsx"
DEFAULT_FILE_PATH = SAMPLE_DATA_DIR / DEFAULT_FILE_NAME