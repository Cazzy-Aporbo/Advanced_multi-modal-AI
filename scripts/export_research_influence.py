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
        ("proof/research-influence.json", "Research influence route outputs."),
        ("proof/research-influence.md", "Readable research influence report."),
    ]
    try:
        from advanced_multimodal_ai.api import create_app

        client = TestClient(create_app())
        bundle = _get(client, "/v1/research/influence")
        harness = _post(client, "/v1/research/harness-improvement", _harness_payload())
        deliberation = _post(
            client,
            "/v1/research/deliberation/assess",
            _deliberation_payload(),
        )
        trust = _post(client, "/v1/research/trust/calibrate", _trust_payload())
        epistemic = _post(
            client,
            "/v1/research/epistemic-risk/assess",
            _epistemic_payload(),
        )

        payload = {
            "bundle": bundle,
            "sample_outputs": {
                "harness_improvement": harness,
                "deliberation_assessment": deliberation,
                "trust_calibration": trust,
                "epistemic_risk": epistemic,
            },
        }

        proof_dir = ROOT / "proof"
        proof_dir.mkdir(parents=True, exist_ok=True)
        json_path = proof_dir / "research-influence.json"
        markdown_path = proof_dir / "research-influence.md"
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
        print(json_path)
        print(markdown_path)
    except Exception as exc:
        finish_script_execution(
            lane="research_influence_export",
            command="python3 scripts/export_research_influence.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="fail",
            notes=[f"Research influence export failed: {exc}"],
        )
        raise
    else:
        finish_script_execution(
            lane="research_influence_export",
            command="python3 scripts/export_research_influence.py",
            artifacts=artifacts,
            started_at=started_at,
            start_counter=start_counter,
            status="pass",
            notes=["Research influence report regenerated from live API routes."],
        )


def _get(client: TestClient, route: str) -> dict:
    response = client.get(route)
    response.raise_for_status()
    return response.json()


def _post(client: TestClient, route: str, payload: dict) -> dict:
    response = client.post(route, json=payload)
    response.raise_for_status()
    return response.json()


def _harness_payload() -> dict:
    return {
        "base_harness_id": "acceptance-spine",
        "minimum_support": 2,
        "protected_invariants": [
            "OpenAPI export remains reproducible",
            "Proof bundle includes generated artifacts",
        ],
        "traces": [
            {
                "trace_id": "proof-run-001",
                "task_family": "proof-export",
                "outcome": "fail",
                "failure_tags": ["stale-proof"],
                "files_touched": ["scripts/export_research_surfaces.py"],
                "verification_commands": ["python3 scripts/export_research_surfaces.py"],
                "notes": "Export changed after API routes moved.",
            },
            {
                "trace_id": "proof-run-002",
                "task_family": "proof-export",
                "outcome": "fail",
                "failure_tags": ["stale-proof"],
                "files_touched": ["proof/research-surfaces.json"],
                "verification_commands": ["python3 scripts/export_research_surfaces.py"],
                "notes": "Proof artifact did not reflect the current backend.",
            },
            {
                "trace_id": "contract-run-001",
                "task_family": "api-contract",
                "outcome": "blocked",
                "failure_tags": ["schema-drift"],
                "files_touched": ["openapi/openapi.json"],
                "verification_commands": ["python3 scripts/export_openapi.py"],
                "notes": "Client surface was not regenerated after contract movement.",
            },
        ],
    }


def _deliberation_payload() -> dict:
    return {
        "decision_id": "domain-transfer-review",
        "domain": "regulated multimodal data",
        "required_roles": ["advocate", "skeptic", "operator", "reviewer"],
        "claims": [
            {
                "role": "advocate",
                "stance": "approve",
                "claim": "The route can proceed because the dataset contract is registered.",
                "evidence_refs": ["catalog:contract-hash", "proof:openapi"],
                "uncertainty": 0.22,
            },
            {
                "role": "skeptic",
                "stance": "investigate",
                "claim": "The route still needs coverage review because tail populations are thin.",
                "evidence_refs": ["music:drift", "profile:coverage"],
                "uncertainty": 0.61,
            },
            {
                "role": "operator",
                "stance": "defer",
                "claim": (
                    "The system should wait until a human reviewer names the "
                    "operational limit."
                ),
                "evidence_refs": ["readiness:human-control"],
                "uncertainty": 0.48,
            },
        ],
    }


def _trust_payload() -> dict:
    return {
        "route": "/v1/industrial/diagnose",
        "purpose": "field diagnostic support",
        "precision": 0.72,
        "human_control": 0.55,
        "oversight": 0.5,
        "validation_evidence": 0.76,
        "reversibility": 0.62,
        "harm_level": "high",
    }


def _epistemic_payload() -> dict:
    repeated_claim = "The catalog is balanced because the average score stayed stable."
    return {
        "assessment_id": "catalog-epistemic-slice",
        "domain": "music and media data",
        "intended_use": "catalog review before recommendation experiments",
        "evidence": [
            {
                "source_id": "metric-001",
                "source_type": "measurement",
                "perspective": "runtime",
                "claim": repeated_claim,
                "confidence": 0.9,
                "uncertainty_visible": False,
                "human_generated": False,
                "age_days": 9,
            },
            {
                "source_id": "metric-002",
                "source_type": "claim",
                "perspective": "runtime",
                "claim": repeated_claim,
                "confidence": 0.86,
                "uncertainty_visible": False,
                "human_generated": False,
                "age_days": 12,
            },
            {
                "source_id": "review-001",
                "source_type": "human_review",
                "perspective": "editorial",
                "claim": "The manifest underrepresents regional instrumentation.",
                "confidence": 0.68,
                "uncertainty_visible": True,
                "human_generated": True,
                "age_days": 3,
            },
            {
                "source_id": "log-001",
                "source_type": "system_log",
                "perspective": "pipeline",
                "claim": "The previous extraction run is older than the current contract.",
                "confidence": 0.74,
                "uncertainty_visible": True,
                "human_generated": False,
                "age_days": 210,
            },
        ],
    }


def _render_markdown(payload: dict) -> str:
    bundle = payload["bundle"]
    samples = payload["sample_outputs"]
    source_rows = "\n".join(
        (f"- **{source['title']}** ({source['year']}) - " f"{'; '.join(source['mechanisms'])}")
        for source in bundle["sources"]
    )
    mechanism_rows = "\n".join(
        (
            f"- **{item['label']}** - `{item['implementation_status']}` - "
            f"score `{item['score']}` - routes: "
            f"{', '.join(item['runtime_routes'])}"
        )
        for item in bundle["mechanisms"]
    )
    proposal_rows = "\n".join(
        (
            f"- **{proposal['proposal_id']}** - `{proposal['status']}` - "
            f"{proposal['expected_behavior']}"
        )
        for proposal in samples["harness_improvement"]["proposals"]
    )
    epistemic_rows = "\n".join(
        (f"- **{item['label']}** - score `{item['score']}` - " f"{item['evidence']}")
        for item in samples["epistemic_risk"]["indicators"]
    )
    return f"""# Research Influence Proof

- Sources: `{bundle['source_count']}`
- Mechanisms: `{bundle['mechanism_count']}`
- Feature surfaces: `{bundle['feature_count']}`
- Routes: `{bundle['route_count']}`
- Tests: `{bundle['test_count']}`

## Sources

{source_rows}

## Mechanisms now represented in code

{mechanism_rows}

## Harness improvement sample

- Failed traces: `{samples['harness_improvement']['failed_trace_count']}`
- Promoted proposals: `{samples['harness_improvement']['promoted_proposal_count']}`

{proposal_rows}

## Deliberation sample

- Recommendation: `{samples['deliberation_assessment']['recommendation']}`
- Disagreement score: `{samples['deliberation_assessment']['disagreement_score']}`
- Missing roles: `{', '.join(samples['deliberation_assessment']['missing_roles']) or 'none'}`

## Trust calibration sample

- Band: `{samples['trust_calibration']['band']}`
- Review required: `{samples['trust_calibration']['review_required']}`
- Score: `{samples['trust_calibration']['score']}`

## Epistemic risk sample

- Band: `{samples['epistemic_risk']['band']}`
- Score: `{samples['epistemic_risk']['score']}`

{epistemic_rows}
"""


if __name__ == "__main__":
    main()
