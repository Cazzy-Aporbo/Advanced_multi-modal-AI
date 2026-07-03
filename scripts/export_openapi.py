from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from advanced_multimodal_ai.api import create_app  # noqa: E402
from advanced_multimodal_ai.execution_journal import (  # noqa: E402
    finish_script_execution,
    script_execution_window,
)


def main() -> None:
    started_at, start_counter = script_execution_window()
    artifacts = [("openapi/openapi.json", "Generated OpenAPI contract.")]
    try:
        output_dir = ROOT / "openapi"
        output_dir.mkdir(parents=True, exist_ok=True)

        app = create_app()
        schema = app.openapi()
        schema["info"]["title"] = "Advanced Multi-modal AI"
        schema["info"]["version"] = app.version

        output_path = output_dir / "openapi.json"
        output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        print(output_path)
    except Exception as exc:
        finish_script_execution(
            lane="openapi_export",
            command="python3 scripts/export_openapi.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"OpenAPI export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="openapi_export",
            command="python3 scripts/export_openapi.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=["OpenAPI contract regenerated."],
        )


if __name__ == "__main__":
    main()
