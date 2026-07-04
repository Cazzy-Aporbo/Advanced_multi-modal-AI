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


def main() -> None:
    started_at, start_counter = script_execution_window()
    artifacts = [
        ("proof/privacy-membrane.json", "Exported privacy membrane proof bundle."),
        ("proof/privacy-membrane.md", "Readable privacy membrane proof bundle."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app

        app = create_app()
        client = TestClient(app)
        sample = client.post(
            "/v1/privacy/deidentify",
            json={
                "text": (
                    "Name: Ana Reyes; email ana.reyes@example.org; "
                    "MRN: MRN-77182; DOB: 1988-10-04; card 4242 4242 4242 4242"
                ),
                "languages": ["en", "fil"],
                "masking_mode": "stable_token",
                "purpose": "proof_export_fixture",
            },
        )
        sample.raise_for_status()
        taxonomy = client.get("/v1/privacy/taxonomy")
        taxonomy.raise_for_status()
        runs = client.get("/v1/privacy/runs", params={"limit": 10})
        runs.raise_for_status()

        payload = {
            "taxonomy": taxonomy.json(),
            "sample_receipt": sample.json()["receipt"],
            "sample_category_summaries": sample.json()["category_summaries"],
            "run_records": runs.json(),
            "notes": [
                "The export is generated from the live API surface.",
                (
                    "The fixture proves masking, receipts, and non-persistence "
                    "without shipping raw sensitive data."
                ),
            ],
        }

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)
        json_path = proof_dir / "privacy-membrane.json"
        markdown_path = proof_dir / "privacy-membrane.md"
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        taxonomy_payload = payload["taxonomy"]
        category_rows = "\n".join(
            (
                f"- `{item['category_id']}` · {item['severity']} · "
                f"{', '.join(item['detector_kinds'])}"
            )
            for item in taxonomy_payload["categories"][:24]
        )
        receipt = payload["sample_receipt"]
        summary_rows = "\n".join(
            (
                f"- `{item['category_id']}` · {item['count']} finding(s) · "
                f"confidence {item['highest_confidence']}"
            )
            for item in payload["sample_category_summaries"]
        )
        markdown = f"""# Privacy Membrane

- Detector version: `{taxonomy_payload['detector_version']}`
- Categories: `{taxonomy_payload['category_count']}`
- Language hints: `{taxonomy_payload['language_count']}`
- Deterministic category coverage: `{taxonomy_payload['deterministic_category_count']}`
- Sample source hash: `{receipt['source_sha256']}`
- Sample redacted hash: `{receipt['redacted_sha256']}`
- Sample finding-set hash: `{receipt['finding_set_sha256']}`

## Boundary notes

{chr(10).join(f"- {note}" for note in taxonomy_payload['boundary_notes'])}

## Sample finding summary

{summary_rows}

## Category register excerpt

{category_rows}
"""
        markdown_path.write_text(markdown, encoding="utf-8")
        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="privacy_membrane_export",
            command="python3 scripts/export_privacy_membrane.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Privacy membrane export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="privacy_membrane_export",
            command="python3 scripts/export_privacy_membrane.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=["Privacy membrane proof regenerated from the live backend."],
        )


if __name__ == "__main__":
    main()
