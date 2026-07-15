import sys
from pathlib import Path

# make `from app...` imports work when pytest runs from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
