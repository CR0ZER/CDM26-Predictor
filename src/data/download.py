import os
import zipfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

os.environ["KAGGLE_USERNAME"] = os.getenv("KAGGLE_USERNAME")
os.environ["KAGGLE_KEY"] = os.getenv("KAGGLE_KEY")

import kaggle

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "international_results": "martj42/international-football-results-from-1872-to-2017",
}

def download_dataset(name: str, slug: str) -> None:
    dest = RAW_DIR / name
    dest.mkdir(exist_ok=True)
    print(f"[download] {name} -> {dest}")
    kaggle.api.dataset_download_files(slug, path=dest, unzip=True)
    print(f"[done] {name}")

if __name__ == "__main__":
    for name, slug in DATASETS.items():
        download_dataset(name, slug)