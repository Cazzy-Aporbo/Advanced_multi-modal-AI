from __future__ import annotations

import json
import sys
from pathlib import Path

from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from advanced_multimodal_ai.execution_journal import (  # noqa: E402
    finish_script_execution,
    script_execution_window,
)


def _anchor_routes_line(item: dict) -> str:
    routes = item.get("anchor_routes") or []
    return ", ".join(f"`{route}`" for route in routes) if routes else "none"


def _proof_surfaces_line(item: dict) -> str:
    surfaces = item.get("proof_surfaces") or []
    return ", ".join(f"`{path}`" for path in surfaces) if surfaces else "none"


def main() -> None:
    started_at, start_counter = script_execution_window()
    artifacts = [
        ("proof/industry-profiles.json", "Exported industry transfer profiles."),
        ("proof/industry-profiles.md", "Readable industry transfer profiles."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app

        app = create_app()
        client = TestClient(app)
        response = client.get("/v1/industries/profiles")
        response.raise_for_status()
        payload = response.json()

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)

        json_path = proof_dir / "industry-profiles.json"
        markdown_path = proof_dir / "industry-profiles.md"

        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        profile_rows = (
            "\n".join(
                (
                    f"## {item['label']}\n\n"
                    f"- modalities: {', '.join(item['primary_modalities'])}\n"
                    f"- anchor routes: {_anchor_routes_line(item)}\n"
                    f"- strict checks: {', '.join(item['strict_checks'])}\n"
                    f"- supply chain focus: {item['supply_chain_focus']}\n"
                    f"- signal questions: {', '.join(item['signal_questions'])}\n"
                    f"- proof surfaces: {_proof_surfaces_line(item)}\n"
                )
                for item in payload["profiles"]
            )
            or "No industry profiles have been exported yet."
        )

        markdown = f"""# Industry Profiles

The runtime lanes can be read across domains without pretending each field has the
same evidence burden. These profiles stay tied to routes and proof surfaces that
already exist in the repository.

{profile_rows}
"""
        markdown_path.write_text(markdown, encoding="utf-8")
        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="industry_profiles_export",
            command="python3 scripts/export_industry_profiles.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Industry profile export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="industry_profiles_export",
            command="python3 scripts/export_industry_profiles.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=[
                "Industry profiles regenerated from the live API and tied back to runtime routes."
            ],
        )


if __name__ == "__main__":
    main()
