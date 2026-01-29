from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from detailed_gui import main  # noqa: E402


if __name__ == "__main__":
    main()
