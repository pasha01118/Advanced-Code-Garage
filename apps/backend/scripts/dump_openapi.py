"""Print FastAPI's live OpenAPI schema as JSON.

Used by CI to detect drift between the backend routes and the committed
contract at packages/contract/openapi.json. No trailing newline is emitted so
the output matches the committed file exactly.
"""

import json
import sys
from pathlib import Path

# Allow running as `python scripts/dump_openapi.py` from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

if __name__ == "__main__":
    sys.stdout.write(json.dumps(app.openapi(), indent=2, sort_keys=False))
