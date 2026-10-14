import sys
from pathlib import Path

# Match the import root used when launching src/app/main.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "app"))
