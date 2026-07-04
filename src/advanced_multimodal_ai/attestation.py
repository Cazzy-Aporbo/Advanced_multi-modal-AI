from __future__ import annotations

import hashlib
from pathlib import Path

from .config import Settings
from .contracts import RuntimeAttestationResponse, VerificationArtifact

REPO_ROOT = Path(__file__).resolve().parents[2]


def build_runtime_attestation(
    settings: Settings,
    store_counts: dict[str, int],
) -> RuntimeAttestationResponse:
    verification_artifacts = [
        _artifact("OpenAPI contract", REPO_ROOT / "openapi" / "openapi.json"),
        _artifact(
            "TypeScript generated client",
            REPO_ROOT / "sdk" / "typescript" / "src" / "generated-openapi.ts",
        ),
        _artifact(
            "Python generated client",
            REPO_ROOT
            / "sdk"
            / "python"
            / "src"
            / "advanced_multimodal_ai_client"
            / "generated_openapi.py",
        ),
        _artifact("Runtime schema", REPO_ROOT / "sql" / "runtime_schema.sql"),
        _artifact("Rust core", REPO_ROOT / "crates" / "multimodal-core" / "Cargo.toml"),
        _artifact(
            "Research surface export",
            REPO_ROOT / "proof" / "research-surfaces.json",
        ),
        _artifact(
            "Repository pulse export",
            REPO_ROOT / "proof" / "repository-pulse.json",
        ),
        _artifact(
            "Repository growth export",
            REPO_ROOT / "proof" / "repository-growth.json",
        ),
        _artifact(
            "Execution journal export",
            REPO_ROOT / "proof" / "execution-journal.json",
        ),
        _artifact(
            "Cymatic surface export",
            REPO_ROOT / "proof" / "cymatic-surface.json",
        ),
        _artifact(
            "Music observatory export",
            REPO_ROOT / "proof" / "music-observatory.json",
        ),
        _artifact(
            "Operator surfaces export",
            REPO_ROOT / "proof" / "operator-surfaces.json",
        ),
        _artifact(
            "Industry profiles export",
            REPO_ROOT / "proof" / "industry-profiles.json",
        ),
        _artifact(
            "Industrial diagnostics export",
            REPO_ROOT / "proof" / "industrial-diagnostics.json",
        ),
        _artifact(
            "Edge topology export",
            REPO_ROOT / "proof" / "edge-topology.json",
        ),
        _artifact(
            "Deployment stack",
            REPO_ROOT / "containers" / "compose.yaml",
        ),
    ]

    return RuntimeAttestationResponse(
        service=settings.service_name,
        version=settings.service_version,
        environment=settings.environment,
        openapi_sha256=_sha256(REPO_ROOT / "openapi" / "openapi.json"),
        store_counts=store_counts,
        supported_lanes=[
            "contract_inference",
            "research_bridge",
            "dataset_catalog",
            "data_lifecycle",
            "change_control",
            "supply_chain_snapshot",
            "connector_ingest",
            "music_manifest",
            "music_feature_warehouse",
            "operator_surfaces",
            "industry_profiles",
            "industrial_diagnostics",
            "edge_gateway",
            "tracking_ledger",
            "deployment_stack",
            "web_ingest",
            "recipe_registry",
            "readiness_report",
            "research_surfaces",
            "repository_pulse",
            "repository_growth",
            "execution_journal",
            "retrieval",
            "video_cleanup",
            "temporal_alignment",
            "drift_baselines",
            "pipeline_ingest",
            "pipeline_export_replay",
            "domain_ontology",
            "liability_surface",
            "bias_taxonomy",
        ],
        verification_artifacts=verification_artifacts,
    )


def _artifact(name: str, path: Path) -> VerificationArtifact:
    status = "present" if path.exists() else "missing"
    detail = str(path.relative_to(REPO_ROOT)) if path.exists() else f"missing: {path.name}"
    return VerificationArtifact(name=name, status=status, detail=detail)


def _sha256(path: Path) -> str:
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()
