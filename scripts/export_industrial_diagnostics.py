from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from advanced_multimodal_ai.execution_journal import (  # noqa: E402
    finish_script_execution,
    script_execution_window,
)
from advanced_multimodal_ai.industrial_diagnostics import (  # noqa: E402
    build_industrial_diagnostic_proof,
)


def main() -> None:
    started_at, start_counter = script_execution_window()
    artifacts = [
        ("proof/industrial-diagnostics.json", "Exported industrial diagnostics bundle."),
        ("proof/industrial-diagnostics.md", "Readable industrial diagnostics bundle."),
    ]
    try:
        payload = build_industrial_diagnostic_proof()
        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)
        json_path = proof_dir / "industrial-diagnostics.json"
        markdown_path = proof_dir / "industrial-diagnostics.md"

        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        markdown_path.write_text(_render_markdown(payload), encoding="utf-8")

        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="industrial_diagnostics_export",
            command="python3 scripts/export_industrial_diagnostics.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Industrial diagnostics export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="industrial_diagnostics_export",
            command="python3 scripts/export_industrial_diagnostics.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=[
                "Industrial diagnostics scenarios, proof tree, and audit chain were regenerated."
            ],
        )


def _render_markdown(payload: dict[str, object]) -> str:
    scenarios = payload["scenarios"]["scenarios"]
    sample_response = payload["sample_response"]
    scenario_rows = "\n".join(
        (
            f"- `{item['scenario_id']}` · `{item['asset_kind']}` · "
            f"{item['label']} · expected {', '.join(item['expected_diagnosis_ids'])}"
        )
        for item in scenarios
    )
    diagnosis_rows = "\n".join(
        (
            f"- `{item['diagnosis_id']}` · {item['severity']} · "
            f"{item['title']} · confidence {item['confidence']}"
        )
        for item in sample_response["diagnoses"]
    )
    compliance_rows = "\n".join(
        (
            f"- `{item['standard']} {item['clause']}` · {item['status']} · "
            f"{item['requirement']}"
        )
        for item in sample_response["compliance_findings"]
    )
    invariant_rows = "\n".join(
        f"- `{item['invariant_id']}` · holds={item['holds']}"
        for item in sample_response["invariants"]
    )
    return f"""# Industrial Diagnostics Bundle

- Sample asset kind: `{sample_response['asset_kind']}`
- Machine family: `{sample_response['machine_family']}`
- Verdict: `{sample_response['verdict']}`
- Diagnoses: `{len(sample_response['diagnoses'])}`
- Compliance findings: `{len(sample_response['compliance_findings'])}`
- Proof nodes: `{len(sample_response['proof_tree'])}`
- Audit entries: `{len(sample_response['audit_trail'])}`

## Scenarios

{scenario_rows}

## Sample diagnoses

{diagnosis_rows}

## Compliance findings

{compliance_rows}

## Invariants

{invariant_rows}
"""


if __name__ == "__main__":
    main()
