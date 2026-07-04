from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .config import Settings
from .contracts import (
    ExecutionJournalSummary,
    ModelResearchCard,
    PulseArtifact,
    PulseLane,
    ReadinessReport,
    RepositoryPulse,
    RuntimeAttestationResponse,
    RuntimeProofBundle,
)
from .repository_growth import load_persisted_repository_growth

REPO_ROOT = Path(__file__).resolve().parents[2]


def build_repository_pulse(
    *,
    settings: Settings,
    attestation: RuntimeAttestationResponse,
    execution_journal: ExecutionJournalSummary,
    proof_bundle: RuntimeProofBundle,
    readiness: ReadinessReport,
    model_cards: list[ModelResearchCard],
) -> RepositoryPulse:
    lanes = [
        _frontend_lane(),
        _community_lane(),
        _backend_lane(attestation=attestation, proof_bundle=proof_bundle),
        _edge_lane(attestation=attestation),
        _music_lane(attestation=attestation),
        _benchmark_lane(),
        _compiled_lane(),
        _client_lane(),
        _operator_lane(),
        _deployment_lane(),
        _evidence_lane(),
        _execution_lane(execution_journal=execution_journal),
        _model_lane(model_cards=model_cards),
    ]

    return RepositoryPulse(
        service=settings.service_name,
        version=settings.service_version,
        route_count=proof_bundle.route_count,
        test_count=proof_bundle.test_count,
        model_count=len(model_cards),
        readiness_posture=readiness.posture,
        lanes=lanes,
    )


def _frontend_lane() -> PulseLane:
    files = [
        "index.html",
        "advanced-technical-portfolio.html",
        "technical-portfolio.html",
        "model-observatory.html",
        "music-observatory.html",
        "field-notes.html",
        "benchmark-observatory.html",
        "cymatic-media-engine.html",
        "industrial-diagnostics.html",
        "industry-profiles.html",
        "industrial-diagnostics.js",
        "cymatic-surface.css",
        "cymatic-surface.js",
        "growth-surface.js",
        "research-surfaces.js",
        "site-controls.css",
        "site-controls.js",
    ]
    artifacts = [_artifact(path, note="Browser-facing surface file.") for path in files]
    return _lane(
        lane_id="frontend_atlas",
        label="Frontend atlas",
        emphasis="frontend",
        summary=(
            "The public site stays downstream from generated proof and "
            "research exports rather than inventing its own runtime story."
        ),
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            "Keep the browser lane reading generated evidence files.",
            "Prefer live bundle hydration over static text repetition.",
        ],
    )


def _community_lane() -> PulseLane:
    persisted = load_persisted_repository_growth()
    files = [
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/use_case.yml",
        ".github/pull_request_template.md",
        "scripts/export_repository_growth.py",
        "proof/repository-growth.json",
        "proof/repository-growth.md",
    ]
    artifacts = [
        _artifact(path, note="Community or repository signal surface.") for path in files
    ]
    stars = int(persisted.get("stars", 0))
    contributors = int(persisted.get("contributor_count", 0))
    proof_exports = len(list((REPO_ROOT / "proof").glob("*.json")))
    score = min(100, 34 + contributors * 4 + len([item for item in artifacts if item.exists]) * 4)
    summary = (
        f"{stars} stars, {contributors} contributors, and {proof_exports} JSON proof exports are "
        "being watched through one quieter repository signal lane."
        if persisted
        else (
            "The repository signal lane is ready to collect GitHub-facing "
            "metrics alongside local proof counts."
        )
    )
    return PulseLane(
        lane_id="community_signals",
        label="Community signals",
        emphasis="evidence",
        live_score=score,
        summary=summary,
        active_count=len([item for item in artifacts if item.exists]),
        warning_count=1 if not persisted else 0,
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            "Keep contribution and security files as concrete as the runtime contracts.",
            "Let repository metrics sit beside proof freshness instead of floating alone.",
        ],
    )


def _benchmark_lane() -> PulseLane:
    files = [
        "src/advanced_multimodal_ai/benchmarks.py",
        "src/advanced_multimodal_ai/service.py",
        "scripts/export_benchmark_surfaces.py",
        "proof/benchmark-surfaces.json",
        "proof/benchmark-surfaces.md",
    ]
    artifacts = [
        _artifact(path, note="Benchmark lane source or generated artifact.") for path in files
    ]
    return _lane(
        lane_id="benchmark_lane",
        label="Reference benchmark lane",
        emphasis="backend",
        summary=(
            "A typed reference workload now exercises connector ingest, "
            "profiling, provenance, batch execution, recipe compilation, "
            "and proof refresh together."
        ),
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            "Keep the benchmark tied to real persisted lanes, not stand-alone timers.",
            "Prefer repeated reference workloads over one-off smoke claims.",
        ],
    )


def _music_lane(*, attestation: RuntimeAttestationResponse) -> PulseLane:
    files = [
        "src/advanced_multimodal_ai/music_features.py",
        "src/advanced_multimodal_ai/music_embeddings.py",
        "src/advanced_multimodal_ai/music_queries.py",
        "src/advanced_multimodal_ai/music_store.py",
        "src/advanced_multimodal_ai/music_truth.py",
        "src/advanced_multimodal_ai/service.py",
        "scripts/export_music_observatory.py",
        "proof/music-observatory.json",
        "proof/music-observatory.md",
    ]
    artifacts = [
        _artifact(path, note="Music manifest, warehouse, or observatory artifact.")
        for path in files
    ]
    manifest_count = attestation.store_counts.get("music_manifests", 0)
    run_count = attestation.store_counts.get("music_feature_runs", 0)
    score = min(100, 32 + manifest_count * 8 + run_count * 10)
    return PulseLane(
        lane_id="music_warehouse",
        label="Music warehouse",
        emphasis="backend",
        live_score=score,
        summary=(
            f"{manifest_count} manifests and {run_count} persisted feature runs now keep the "
            "sound lane downstream from contracts, provenance, and Parquet output."
        ),
        active_count=manifest_count + run_count,
        warning_count=1 if run_count == 0 else 0,
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            "Keep raw media outside the repository and derived features inside the proof path.",
            "Let multilingual, regional, genre, and drift coverage grow "
            "through manifests rather than hand-waving.",
        ],
    )


def _edge_lane(*, attestation: RuntimeAttestationResponse) -> PulseLane:
    files = [
        "src/advanced_multimodal_ai/edge_gateway.py",
        "src/advanced_multimodal_ai/tracking_ledger.py",
        "src/advanced_multimodal_ai/vector_mesh.py",
        "scripts/export_edge_topology.py",
        "proof/edge-topology.json",
        "proof/edge-topology.md",
    ]
    artifacts = [
        _artifact(path, note="Edge gateway, ledger, or exported topology artifact.")
        for path in files
    ]
    event_count = attestation.store_counts.get("edge_packets", 0)
    score = min(100, 40 + event_count * 12)
    return PulseLane(
        lane_id="edge_gateway",
        label="Edge gateway",
        emphasis="backend",
        live_score=score,
        summary=(
            f"{event_count} persisted edge packet events now show how packet geometry, "
            "cross-border posture, and routing decisions are carried into an append-only ledger."
        ),
        active_count=event_count,
        warning_count=1 if event_count == 0 else 0,
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            "Keep gateway evaluations tied to typed packet contracts rather than loose JSON blobs.",
            (
                "Use the ledger to show where routing decisions came from before "
                "widening the control plane."
            ),
        ],
    )


def _backend_lane(
    *,
    attestation: RuntimeAttestationResponse,
    proof_bundle: RuntimeProofBundle,
) -> PulseLane:
    files = [
        "src/advanced_multimodal_ai/api.py",
        "src/advanced_multimodal_ai/service.py",
        "src/advanced_multimodal_ai/connectors.py",
        "src/advanced_multimodal_ai/pipelines.py",
        "src/advanced_multimodal_ai/quality.py",
        "src/advanced_multimodal_ai/stewardship_store.py",
        "src/advanced_multimodal_ai/repository_pulse.py",
    ]
    artifacts = [_artifact(path, note="Backend runtime source file.") for path in files]
    active_count = (
        proof_bundle.route_count
        + attestation.store_counts.get("connector_runs", 0)
        + attestation.store_counts.get("pipeline_runs", 0)
    )
    warning_count = sum(
        1
        for store in ("connector_runs", "pipeline_runs", "ontology_snapshots")
        if attestation.store_counts.get(store, 0) == 0
    )
    score = min(100, 45 + proof_bundle.route_count + len(attestation.store_counts) * 2)
    return PulseLane(
        lane_id="runtime_backend",
        label="Runtime backend",
        emphasis="backend",
        live_score=score,
        summary=(
            f"{proof_bundle.route_count} routes, {proof_bundle.test_count} "
            "tests, and persisted governance stores keep the API lane active."
        ),
        active_count=active_count,
        warning_count=warning_count,
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            "Keep connector and replay evidence accumulating under varied inputs.",
            "Let governance stores grow beside active route traces.",
        ],
    )


def _compiled_lane() -> PulseLane:
    files = [
        "crates/multimodal-core/Cargo.toml",
        "crates/multimodal-core/src/lib.rs",
        "src/advanced_multimodal_ai/rust_bridge.py",
    ]
    artifacts = [
        _artifact(
            path,
            note=(
                "Compiled signal primitive."
                if "multimodal-core" in path
                else "Python bridge into the compiled core."
            ),
        )
        for path in files
    ]
    return _lane(
        lane_id="compiled_core",
        label="Compiled core",
        emphasis="compiled",
        summary=(
            "Deterministic signal work stays in a compiled lane and remains "
            "reachable through a small Python bridge."
        ),
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            "Keep the compiled lane narrow and measured.",
            "Add new Rust only where deterministic math or replay earns it.",
        ],
    )


def _client_lane() -> PulseLane:
    files = [
        "openapi/openapi.json",
        "sdk/python/src/advanced_multimodal_ai_client/generated_openapi.py",
        "sdk/typescript/src/generated-openapi.ts",
        "sdk/typescript/package.json",
    ]
    artifacts = [_artifact(path, note="Client or contract artifact.") for path in files]
    return _lane(
        lane_id="generated_clients",
        label="Generated clients",
        emphasis="client",
        summary=(
            "The Python and TypeScript client surfaces are generated from the "
            "live contract rather than maintained as parallel lore."
        ),
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            "Regenerate client surfaces whenever the API contract moves.",
            "Keep TypeScript compilation in the proof path.",
        ],
    )


def _deployment_lane() -> PulseLane:
    files = [
        "Dockerfile",
        "Makefile",
        "containers/compose.yaml",
        "containers/clickhouse-init.sql",
    ]
    artifacts = [_artifact(path, note="Deployment or local stack artifact.") for path in files]
    return _lane(
        lane_id="deployment_stack",
        label="Deployment stack",
        emphasis="client",
        summary=(
            "Container, local stack, and command surfaces now sit beside the runtime edge "
            "instead of being implied by prose alone."
        ),
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            (
                "Keep the stack definition explicit, versioned, and smaller than the "
                "claims built on top of it."
            ),
            "Let compose, Docker, and Make targets point at the same bounded runtime story.",
        ],
    )


def _evidence_lane() -> PulseLane:
    files = [
        "proof/runtime-proof.json",
        "proof/readiness-report.json",
        "proof/example-bundle.json",
        "proof/benchmark-surfaces.json",
        "proof/cymatic-surface.json",
        "proof/music-observatory.json",
        "proof/research-surfaces.json",
        "proof/execution-journal.json",
        "scripts/build_runtime_proof_bundle.py",
        "scripts/export_benchmark_surfaces.py",
        "scripts/export_cymatic_surface.py",
        "scripts/export_execution_journal.py",
        "scripts/export_music_observatory.py",
        "scripts/export_readiness_report.py",
        "scripts/export_example_bundle.py",
        "scripts/export_research_surfaces.py",
    ]
    artifacts = [_artifact(path, note="Exported proof or export script.") for path in files]
    return _lane(
        lane_id="evidence_exports",
        label="Evidence exports",
        emphasis="evidence",
        summary=(
            "Proof, readiness, worked examples, and research surfaces can be "
            "regenerated as files the public site reads directly."
        ),
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            "Keep exports close to CI and local verification.",
            "Prefer regenerated artifacts to hand-edited summaries.",
        ],
    )


def _execution_lane(*, execution_journal: ExecutionJournalSummary) -> PulseLane:
    files = [
        "src/advanced_multimodal_ai/execution_journal.py",
        "src/advanced_multimodal_ai/execution_journal_store.py",
        "proof/execution-journal.json",
        "proof/execution-journal.md",
    ]
    artifacts = [_artifact(path, note="Execution-memory file or export.") for path in files]
    score = min(100, 30 + execution_journal.total_runs * 6)
    return PulseLane(
        lane_id="execution_history",
        label="Execution history",
        emphasis="evidence",
        live_score=score,
        summary=(
            f"{execution_journal.total_runs} persisted script runs now leave "
            "a reusable memory of what exported, what passed, and what files changed."
        ),
        active_count=execution_journal.passing_runs,
        warning_count=execution_journal.failing_runs,
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            "Let export and verification lanes keep writing their own receipts.",
            "Use repeated runs to show operational continuity, not one-time polish.",
        ],
    )


def _model_lane(*, model_cards: list[ModelResearchCard]) -> PulseLane:
    files = sorted({card.source_file for card in model_cards})
    artifacts = [
        _artifact(
            path,
            note=(
                "Runtime-ready model file."
                if any(card.source_file == path and card.runtime_ready for card in model_cards)
                else "Research model file."
            ),
        )
        for path in files
    ]
    runtime_ready_count = sum(1 for card in model_cards if card.runtime_ready)
    score = min(100, 35 + runtime_ready_count * 12 + len(model_cards) * 5)
    return PulseLane(
        lane_id="model_registry",
        label="Model registry",
        emphasis="models",
        live_score=score,
        summary=(
            f"{runtime_ready_count} of {len(model_cards)} named models are "
            "runtime-ready in the current environment."
        ),
        active_count=len(model_cards),
        warning_count=max(0, len(model_cards) - runtime_ready_count),
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            "Promote research models only when proof and replay back them.",
            "Keep model notes honest about what is live and what is still exploratory.",
        ],
    )


def _operator_lane() -> PulseLane:
    files = [
        "src/advanced_multimodal_ai/operator_surfaces.py",
        "src/advanced_multimodal_ai/api.py",
        "scripts/export_operator_surfaces.py",
        "proof/operator-surfaces.json",
        "proof/operator-surfaces.md",
    ]
    artifacts = [
        _artifact(path, note="Operator surface source or generated artifact.") for path in files
    ]
    return _lane(
        lane_id="operator_surface",
        label="Operator surface",
        emphasis="compiled",
        summary=(
            "Typed command, skill, plugin, and speech-task surfaces keep the "
            "repository's improvement and execution lanes readable as one system."
        ),
        files=files,
        artifacts=artifacts,
        suggested_actions=[
            "Keep operator cards tied to real routes, files, and proof artifacts.",
            "Prefer inspect-plan-run-verify loops over hand-written capability claims.",
        ],
    )


def _lane(
    *,
    lane_id: str,
    label: str,
    emphasis: str,
    summary: str,
    files: list[str],
    artifacts: list[PulseArtifact],
    suggested_actions: list[str],
) -> PulseLane:
    active_count = sum(1 for artifact in artifacts if artifact.exists)
    warning_count = sum(1 for artifact in artifacts if artifact.status != "pass")
    live_score = round((active_count / len(artifacts)) * 100) if artifacts else 0
    return PulseLane(
        lane_id=lane_id,
        label=label,
        emphasis=emphasis,
        live_score=live_score,
        summary=summary,
        active_count=active_count,
        warning_count=warning_count,
        files=files,
        artifacts=artifacts,
        suggested_actions=suggested_actions,
    )


def _artifact(path_text: str, *, note: str) -> PulseArtifact:
    path = REPO_ROOT / path_text
    if not path.exists():
        return PulseArtifact(
            label=path.name,
            path=path_text,
            exists=False,
            status="missing",
            note=note,
        )

    stats = path.stat()
    modified_at = datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat()
    return PulseArtifact(
        label=path.name,
        path=path_text,
        exists=True,
        bytes=stats.st_size,
        modified_at=modified_at,
        status="pass",
        note=note,
    )
