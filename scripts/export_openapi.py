from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from advanced_multimodal_ai.api import create_app  # noqa: E402


def main() -> None:
    output_dir = ROOT / "openapi"
    output_dir.mkdir(parents=True, exist_ok=True)

    app = create_app()
    schema = app.openapi()
    schema["info"]["title"] = "Advanced Multi-modal AI"
    schema["info"]["version"] = app.version

    output_path = output_dir / "openapi.json"
    output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
