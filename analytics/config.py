from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Where analytics tables will be saved
OUTPUT_DIR = BASE_DIR / "analytics_tables"

# Ensure folder exists
OUTPUT_DIR.mkdir(exist_ok=True)