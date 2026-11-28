"""
Shared pytest setup.

* Tests always run against a throw-away SQLite database, never the real Postgres
  (even inside the backend container where DATABASE_URL points to Postgres).
  Set TEST_DATABASE_URL to use another database on purpose.
* MEDIA_DIR points to a temporary folder.
* SAMPLE_APKG: path of the sample Anki deck in the repository (tests that need it
  are skipped when it is not available, e.g. inside the Docker image).
"""

import os
import sys
import tempfile
from pathlib import Path

_TEST_DB = Path(tempfile.gettempdir()) / "memora_pytest.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite+aiosqlite:///{_TEST_DB}")
# Media extracted by import tests goes to a temp folder, not into the repository
os.environ["MEDIA_DIR"] = tempfile.mkdtemp(prefix="memora_pytest_media_")

# Make "import app" work whether pytest runs from the repo root or from backend/
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

SAMPLE_APKG = BACKEND_DIR.parent / "Anki_format_datasets" / "Tieng_Nhat_Tong_hop_N1_to_N5.apkg"
