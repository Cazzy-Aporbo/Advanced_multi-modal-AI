from __future__ import annotations

from pathlib import Path
from typing import Iterable, get_args

from .contracts import (
    ConnectorKind,
    RuntimeAttestationResponse,
    RuntimeProofBundle,
    VerificationCommand,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def build_runtime_proof_bundle(
    *,
    attestation: RuntimeAttestationResponse,
    route_count: int,
) -> RuntimeProofBundle:
    return RuntimeProofBundle(
        service=attestation.service,
        version=attestation.version,
        environment=attestation.environment,
        route_count=route_count,
        test_count=_count_test_functions(REPO_ROOT / "tests"),
        verification_artifact_count=len(attestation.verification_artifacts),
        connector_kinds=list(get_args(ConnectorKind)),
        supported_lanes=attestation.supported_lanes,
        store_counts=attestation.store_counts,
        verification_commands=[
            VerificationCommand(
                label="lint",
                command="python3 -m ruff check src tests scripts",
            ),
            VerificationCommand(
                label="tests",
                command="python3 -m pytest -q",
            ),
            VerificationCommand(
                label="property-fuzz",
                command="python3 -m pytest -q tests/test_property_fuzz.py",
            ),
            VerificationCommand(
                label="rust",
                command="cargo test -p multimodal-core",
            ),
            VerificationCommand(
                label="openapi",
                command="python3 scripts/export_openapi.py",
            ),
            VerificationCommand(
                label="sdk",
                command="python3 scripts/generate_sdk_surfaces.py",
            ),
            VerificationCommand(
                label="research-surfaces",
                command="python3 scripts/export_research_surfaces.py",
            ),
            VerificationCommand(
                label="repository-pulse",
                command="python3 scripts/export_repository_pulse.py",
            ),
            VerificationCommand(
                label="repository-growth",
                command="python3 scripts/export_repository_growth.py",
            ),
            VerificationCommand(
                label="benchmark-surfaces",
                command="python3 scripts/export_benchmark_surfaces.py",
            ),
            VerificationCommand(
                label="cymatic-surface",
                command="python3 scripts/export_cymatic_surface.py",
            ),
            VerificationCommand(
                label="music-observatory",
                command="python3 scripts/export_music_observatory.py",
            ),
            VerificationCommand(
                label="operator-surfaces",
                command="python3 scripts/export_operator_surfaces.py",
            ),
            VerificationCommand(
                label="industry-profiles",
                command="python3 scripts/export_industry_profiles.py",
            ),
            VerificationCommand(
                label="industrial-diagnostics",
                command="python3 scripts/export_industrial_diagnostics.py",
            ),
            VerificationCommand(
                label="edge-topology",
                command="python3 scripts/export_edge_topology.py",
            ),
            VerificationCommand(
                label="execution-journal",
                command="python3 scripts/export_execution_journal.py",
            ),
            VerificationCommand(
                label="acceptance",
                command="python3 scripts/run_acceptance_spine.py",
            ),
            VerificationCommand(
                label="readiness",
                command="python3 scripts/export_readiness_report.py",
            ),
            VerificationCommand(
                label="examples",
                command="python3 scripts/export_example_bundle.py",
            ),
            VerificationCommand(
                label="typescript",
                command="npm run --prefix sdk/typescript check",
            ),
        ],
        verification_artifacts=attestation.verification_artifacts,
    )


def _count_test_functions(tests_root: Path) -> int:
    if not tests_root.exists():
        return 0
    total = 0
    for path in tests_root.rglob("test_*.py"):
        lines = path.read_text(encoding="utf-8").splitlines()
        total += _count_prefixed_lines(lines, "def test_")
        total += _count_prefixed_lines(lines, "async def test_")
    return total


def _count_prefixed_lines(lines: Iterable[str], prefix: str) -> int:
    return sum(1 for line in lines if line.lstrip().startswith(prefix))
