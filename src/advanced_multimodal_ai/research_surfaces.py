from __future__ import annotations

from typing import Dict, List

from .contracts import (
    ArchitectureLane,
    ModelResearchCard,
    ModelResearchQuestion,
    ReadinessReport,
    RegisteredModelResponse,
    RepositoryConnection,
    RepositoryFinding,
    ResearchSurfaceBundle,
    ResearchSurfaceSummary,
    RuntimeAttestationResponse,
    RuntimeProofBundle,
)

MODEL_RESEARCH_NOTES: Dict[str, Dict[str, object]] = {
    "adaptive_transformer": {
        "role_in_system": (
            "The main bridge between the contract-safe tensor edge and the broader "
            "research archive."
        ),
        "why_used": (
            "It gives the repository one serious multimodal model that can be discussed "
            "in terms of routing, fusion discipline, and uncertainty without requiring "
            "the public runtime to pretend every research branch is production-ready."
        ),
        "strengths": [
            (
                "Handles uneven modality mixtures without requiring every lane "
                "to be equally rich."
            ),
            "Keeps hierarchical fusion visible enough to study where signal loss begins.",
            "Supports contract-mode summaries beside research-mode exploration.",
        ],
        "limits": [
            (
                "Still needs broader paired data before its behavior on long "
                "video-heavy work is persuasive."
            ),
            (
                "Runtime evidence is stronger on tensor orchestration than on "
                "full-scale training outcomes."
            ),
            "Calibration remains modest unless uncertainty output is explicitly exercised.",
        ],
        "improvement_paths": [
            (
                "Add evaluated transcript-plus-frame corpora with stronger "
                "long-range temporal supervision."
            ),
            "Track calibration error and abstention behavior as first-class benchmark outputs.",
            "Compare its fusion posture against narrower baselines under population-entry drift.",
        ],
        "evidence_surfaces": [
            "/v1/infer",
            "/v1/stream",
            "/v1/data/profile",
            "/v1/drift/check",
        ],
        "related_files": [
            "dynamic_transformer.py",
            "src/advanced_multimodal_ai/service.py",
            "src/advanced_multimodal_ai/quality.py",
            "src/advanced_multimodal_ai/drift.py",
        ],
        "open_questions": [
            {
                "prompt": (
                    "When does hierarchical fusion help more than it hides "
                    "weak modality evidence?"
                ),
                "why_it_matters": (
                    "A multimodal model can appear impressive while quietly leaning too hard "
                    "on the easiest modality in the room."
                ),
                "current_position": (
                    "The repository now measures entropy, sparsity, and alignment before fusion, "
                    "but it still needs richer comparative evaluation sets."
                ),
            },
            {
                "prompt": "What should count as enough uncertainty to hold a result back?",
                "why_it_matters": (
                    "Confidence without a stopping rule is not especially helpful in a live system."
                ),
                "current_position": (
                    "Uncertainty can be surfaced, though the evidence story is stronger than the "
                    "current threshold policy."
                ),
            },
        ],
    },
    "complete_multimodal": {
        "role_in_system": (
            "A larger research archive model that shows the full ambition of the repository, "
            "including memory and training-oriented helpers."
        ),
        "why_used": (
            "It preserves the broader design vocabulary of the project without forcing the public "
            "runtime to overstate what it can execute every day."
        ),
        "strengths": [
            "Shows how modality-specific encoders, routing, and memory can be studied together.",
            "Makes the repository useful as a learning surface for end-to-end multimodal design.",
            "Keeps the research ambition visible even when the runtime edge stays narrow.",
        ],
        "limits": [
            "Too broad to treat as the default live edge without much stronger field evidence.",
            (
                "Training helpers are present, though the repo is still better "
                "at runtime proof than large-scale training proof."
            ),
            "Needs more dataset-specific evaluation before its claims should travel very far.",
        ],
        "improvement_paths": [
            "Attach explicit benchmark suites for memory-heavy multimodal tasks.",
            "Document which subsystems are stable enough to graduate into the core runtime.",
            "Add stronger supply-path evidence for large batch training data movement.",
        ],
        "evidence_surfaces": [
            "/v1/models",
            "/v1/recipes/compile",
            "/v1/catalog/register",
            "/v1/runtime/attestation",
        ],
        "related_files": [
            "complete_model.py",
            "src/advanced_multimodal_ai/recipes.py",
            "src/advanced_multimodal_ai/catalog.py",
            "src/advanced_multimodal_ai/attestation.py",
        ],
        "open_questions": [
            {
                "prompt": (
                    "Which parts of the larger research model deserve "
                    "promotion into the runtime edge?"
                ),
                "why_it_matters": (
                    "A generous archive is useful, but only if the repo is "
                    "honest about which pieces have earned operational trust."
                ),
                "current_position": (
                    "The bridge exists. The next step is clearer promotion "
                    "criteria tied to proof and replay."
                ),
            },
        ],
    },
    "fusion_lab": {
        "role_in_system": (
            "A comparative lane for studying how modalities are combined "
            "rather than assuming one fusion style suits every problem."
        ),
        "why_used": (
            "Fusion is usually where multimodal work becomes vague. Keeping it "
            "modular makes the tradeoffs easier to inspect and harder to "
            "romanticize."
        ),
        "strengths": [
            (
                "Lets the repository compare concatenation, gated fusion, "
                "bilinear pooling, and hierarchical mixing."
            ),
            "Supports learning and ablation work without disturbing the public API edge.",
            (
                "Makes it easier to reason about model behavior in terms of "
                "mechanism rather than branding."
            ),
        ],
        "limits": [
            "It is a lab lane, not a standalone evaluated system.",
            (
                "It needs more paired benchmarks to show when one fusion path "
                "clearly outperforms another."
            ),
        ],
        "improvement_paths": [
            "Attach benchmark matrices showing where each fusion path fails or overfits.",
            (
                "Bring replay evidence and drift posture into fusion "
                "comparisons, not only top-line outputs."
            ),
        ],
        "evidence_surfaces": [
            "/v1/data/profile",
            "/v1/pipelines/runs/{run_id}/replay",
        ],
        "related_files": [
            "fusion_strategies.py",
            "src/advanced_multimodal_ai/quality.py",
            "src/advanced_multimodal_ai/replay.py",
        ],
        "open_questions": [
            {
                "prompt": (
                    "How much fusion complexity is actually helpful before it "
                    "starts hiding fragile evidence?"
                ),
                "why_it_matters": (
                    "More machinery can look clever while making failure harder to see."
                ),
                "current_position": (
                    "The repository is better at exposing the options than at "
                    "ranking them under shared benchmarks."
                ),
            },
        ],
    },
    "attention_core": {
        "role_in_system": (
            "A lower-level mechanism lane for cross-modal and sparse attention experiments."
        ),
        "why_used": (
            "Attention primitives matter here because the project is "
            "interested in where cross-modal context is genuinely useful and "
            "where it merely makes the system harder to explain."
        ),
        "strengths": [
            (
                "Keeps attention work inspectable instead of burying it inside "
                "a single large model file."
            ),
            "Supports experimentation with sparse and cross-modal routing ideas.",
        ],
        "limits": [
            "It is a mechanism library rather than a measured endpoint on its own.",
            (
                "Without richer task-level evaluation, it teaches architecture "
                "more than it proves performance."
            ),
        ],
        "improvement_paths": [
            (
                "Connect attention experiments to benchmark deltas instead of "
                "architectural description alone."
            ),
            "Add clearer ablation outputs showing what each attention change bought or cost.",
        ],
        "evidence_surfaces": [
            "/v1/models",
            "/v1/proof/bundle",
        ],
        "related_files": [
            "core/attention_mechanisms.py",
            "dynamic_transformer.py",
            "complete_model.py",
        ],
        "open_questions": [
            {
                "prompt": "Which attention variations survive contact with noisy multimodal data?",
                "why_it_matters": (
                    "Elegant attention code can still collapse once the "
                    "modalities stop cooperating."
                ),
                "current_position": (
                    "The repository names the mechanisms clearly. It still "
                    "needs more field-shaped comparisons."
                ),
            },
        ],
    },
}


def build_model_research_cards(
    *, registered_models: List[RegisteredModelResponse]
) -> List[ModelResearchCard]:
    cards: List[ModelResearchCard] = []
    for model in registered_models:
        notes = MODEL_RESEARCH_NOTES.get(model.model_id, {})
        question_payloads = notes.get("open_questions", [])
        cards.append(
            ModelResearchCard(
                model_id=model.model_id,
                label=model.label,
                source_file=model.source_file,
                runtime_ready=model.runtime_ready,
                supports_contract_mode=model.supports_contract_mode,
                supports_research_mode=model.supports_research_mode,
                role_in_system=str(notes.get("role_in_system", model.notes)),
                why_used=str(notes.get("why_used", model.notes)),
                strengths=[str(item) for item in notes.get("strengths", [])],
                limits=[str(item) for item in notes.get("limits", [])],
                improvement_paths=[
                    str(item) for item in notes.get("improvement_paths", [])
                ],
                evidence_surfaces=[
                    str(item) for item in notes.get("evidence_surfaces", [])
                ],
                related_files=[str(item) for item in notes.get("related_files", [])],
                open_questions=[
                    ModelResearchQuestion.model_validate(item)
                    for item in question_payloads
                ],
            )
        )
    return cards


def build_repository_connections() -> List[RepositoryConnection]:
    return [
        RepositoryConnection(
            connection_id="rows-to-batches",
            title=(
                "Rows become batches through typed evidence, not through "
                "silent reshaping"
            ),
            summary=(
                "The intake path begins in connectors.py, becomes a dataset "
                "contract in catalog.py, and only then moves into "
                "pipelines.py where modality batches are assembled."
            ),
            files=[
                "src/advanced_multimodal_ai/connectors.py",
                "src/advanced_multimodal_ai/catalog.py",
                "src/advanced_multimodal_ai/pipelines.py",
            ],
            api_surfaces=[
                "/v1/connectors/register",
                "/v1/connectors/pipeline-ingest",
                "/v1/catalog/register",
            ],
            learning_value=(
                "It shows how to keep ingestion, schema care, and tensor "
                "preparation in one chain without hiding the transformations."
            ),
            watch_points=[
                (
                    "Too many dropped rows usually means the modality mapping "
                    "is doing more damage than help."
                ),
                (
                    "A dataset contract should be registered before batch "
                    "work becomes the default path."
                ),
            ],
        ),
        RepositoryConnection(
            connection_id="music-manifest-to-warehouse",
            title="Audio manifests become a warehouse without dragging raw media into git",
            summary=(
                "music_store.py records track identity, rights posture, and source provenance; "
                "music_features.py, music_embeddings.py, and music_truth.py then turn that track "
                "into segment maps, derived feature tables, receipts, and queryable drift evidence."
            ),
            files=[
                "src/advanced_multimodal_ai/music_store.py",
                "src/advanced_multimodal_ai/music_features.py",
                "src/advanced_multimodal_ai/music_embeddings.py",
                "src/advanced_multimodal_ai/music_truth.py",
                "src/advanced_multimodal_ai/service.py",
                "scripts/export_music_observatory.py",
            ],
            api_surfaces=[
                "/v1/music/manifests",
                "/v1/music/features/extract",
                "/v1/music/overview",
                "/v1/music/drift",
                "/v1/music/proof/change-report",
            ],
            learning_value=(
                "This is where the repository shows how to keep sound work auditable, "
                "segmented, and reusable without pretending every reviewer needs the raw media."
            ),
            watch_points=[
                (
                    "A feature table is only useful if its extraction version "
                    "and source fingerprint stay attached."
                ),
                (
                    "Genre and language counts become brittle if the "
                    "manifest lane is treated as optional."
                ),
                (
                    "Alignment windows need transcript and frame references "
                    "if one moment is meant to survive across modalities."
                ),
            ],
        ),
        RepositoryConnection(
            connection_id="measurement-before-fusion",
            title="Measurement sits in front of inference instead of apologizing after it",
            summary=(
                "quality.py, signal_math.py, provenance.py, and alignment.py "
                "give the runtime a chance to say what it knows about the data "
                "before service.py turns that data into output."
            ),
            files=[
                "src/advanced_multimodal_ai/quality.py",
                "src/advanced_multimodal_ai/signal_math.py",
                "src/advanced_multimodal_ai/provenance.py",
                "src/advanced_multimodal_ai/alignment.py",
                "src/advanced_multimodal_ai/service.py",
            ],
            api_surfaces=[
                "/v1/data/profile",
                "/v1/data/provenance",
                "/v1/alignment/windows",
                "/v1/infer",
            ],
            learning_value=(
                "This is where the repository becomes useful for people who "
                "care how a signal was treated, not only what a model "
                "eventually returned."
            ),
            watch_points=[
                "High fusion readiness with weak provenance is still a fragile surface.",
                "Alignment windows are only persuasive when the original timing remains intact.",
            ],
        ),
        RepositoryConnection(
            connection_id="review-beside-runtime",
            title="Drift, stewardship, and liability remain part of the same backend story",
            summary=(
                "drift.py, stewardship_store.py, domain_ontology.py, and "
                "liability_surface.py keep review work close to the routes "
                "that need it."
            ),
            files=[
                "src/advanced_multimodal_ai/drift.py",
                "src/advanced_multimodal_ai/stewardship_store.py",
                "src/advanced_multimodal_ai/domain_ontology.py",
                "src/advanced_multimodal_ai/liability_surface.py",
            ],
            api_surfaces=[
                "/v1/drift/check",
                "/v1/stewardship/posture",
                "/v1/ontology/ingest",
                "/v1/ontology/liability",
            ],
            learning_value=(
                "The repo is more credible when data retirement, cross-border "
                "movement, and route mismatch can be inspected through code "
                "rather than left to policy prose alone."
            ),
            watch_points=[
                "A drift baseline without a review rhythm becomes decoration quickly.",
                "Cross-border edges deserve the same specificity as model inputs do.",
            ],
        ),
        RepositoryConnection(
            connection_id="proof-to-client",
            title="Proof, OpenAPI export, and SDK generation share one source of truth",
            summary=(
                "attestation.py and proof.py describe what is present; export "
                "scripts then freeze the public contract into generated Python "
                "and TypeScript surfaces."
            ),
            files=[
                "src/advanced_multimodal_ai/attestation.py",
                "src/advanced_multimodal_ai/proof.py",
                "scripts/export_openapi.py",
                "scripts/generate_sdk_surfaces.py",
            ],
            api_surfaces=[
                "/v1/runtime/attestation",
                "/v1/proof/bundle",
                "/v1/readiness/report",
            ],
            learning_value=(
                "It shows how documentation and client packaging can stay "
                "tethered to a live contract instead of becoming separate "
                "stories."
            ),
            watch_points=[
                (
                    "Generated clients should be regenerated when the contract "
                    "moves, not only before release."
                ),
                (
                    "Proof is more useful when it counts real stores, routes, "
                    "and artifacts rather than generic claims."
                ),
            ],
        ),
        RepositoryConnection(
            connection_id="connector-proof-benchmark",
            title=(
                "Connector proof, batch work, and recipe handoff can now "
                "be exercised in one repeatable lane"
            ),
            summary=(
                "benchmarks.py and service.py now use the same connector, profiling, "
                "job, recipe, and proof surfaces the runtime already exposes, then publish "
                "the result as a generated benchmark artifact."
            ),
            files=[
                "src/advanced_multimodal_ai/benchmarks.py",
                "src/advanced_multimodal_ai/service.py",
                "scripts/export_benchmark_surfaces.py",
                "proof/benchmark-surfaces.json",
            ],
            api_surfaces=[
                "/v1/benchmarks/reference",
                "/v1/connectors/pipeline-ingest",
                "/v1/jobs/batch-infer",
                "/v1/recipes/compile",
            ],
            learning_value=(
                "This connection makes the repository easier to trust because the "
                "same operational lanes are exercised together instead of being admired separately."
            ),
            watch_points=[
                (
                    "Reference workloads should stay deterministic and readable, "
                    "not drift into decorative microbenchmarks."
                ),
                (
                    "Batch concurrency is useful only when per-item failures "
                    "stay visible in the stored record."
                ),
            ],
        ),
    ]


def build_architecture_lanes() -> List[ArchitectureLane]:
    return [
        ArchitectureLane(
            lane_id="atlas_frontend",
            label="Atlas and public study surfaces",
            layer="frontend",
            purpose=(
                "Translate runtime proof, model notes, and research findings "
                "into readable public pages without moving inference into the browser."
            ),
            directories=[
                "index.html",
                "advanced-technical-portfolio.html",
                "technical-portfolio.html",
                "model-observatory.html",
                "field-notes.html",
                "benchmark-observatory.html",
                "cymatic-media-engine.html",
                "cymatic-surface.css",
                "cymatic-surface.js",
                "research-surfaces.js",
            ],
            entry_surfaces=[
                "proof/research-surfaces.json",
                "proof/runtime-proof.json",
                "proof/readiness-report.json",
                "proof/benchmark-surfaces.json",
                "proof/cymatic-surface.json",
            ],
            outputs=[
                "Signal Atlas",
                "Architecture Surface",
                "Component Catalog",
                "Model Observatory",
                "Field Notes",
                "Benchmark Observatory",
                "Cymatic Media Engine",
            ],
            proof_points=[
                "Generated proof exports are read directly by the browser lane.",
                "The atlas remains a display surface rather than a silent compute fork.",
            ],
            why_it_exists=(
                "The public pages should stay legible and alive while remaining "
                "downstream from the backend source of truth."
            ),
        ),
        ArchitectureLane(
            lane_id="music_warehouse",
            label="Music manifest and feature warehouse",
            layer="backend",
            purpose=(
                "Hold manifest-only audio intake, stable segment indexing, "
                "derived feature extraction, "
                "Parquet persistence, and the public music observatory in one reproducible lane."
            ),
            directories=[
                "src/advanced_multimodal_ai/music_store.py",
                "src/advanced_multimodal_ai/music_features.py",
                "src/advanced_multimodal_ai/music_embeddings.py",
                "src/advanced_multimodal_ai/music_queries.py",
                "src/advanced_multimodal_ai/music_truth.py",
                "scripts/export_music_observatory.py",
                "music-observatory.html",
            ],
            entry_surfaces=[
                "/v1/music/manifests",
                "/v1/music/features/extract",
                "/v1/music/overview",
                "/v1/music/features/query",
                "/v1/music/alignment",
                "/v1/music/drift",
                "/v1/music/proof/change-report",
                "proof/music-observatory.json",
            ],
            outputs=[
                "manifest records",
                "segment-aligned derived feature tables",
                "embedding receipts",
                "drift indicators",
                "change-proof narratives",
                "persisted feature run receipts",
                "music observatory export",
            ],
            proof_points=[
                (
                    "The lane stores manifests and derived Parquet output "
                    "without committing raw media."
                ),
                (
                    "Feature runs can be reopened through persisted "
                    "records, Arrow-backed feature slices, and exported proof."
                ),
            ],
            why_it_exists=(
                "A serious sound lane needs more than visual reactivity. "
                "It needs identity, segmentation, "
                "feature memory, and a clear record of what was measured."
            ),
        ),
        ArchitectureLane(
            lane_id="runtime_backend",
            label="Runtime API and orchestration spine",
            layer="backend",
            purpose=(
                "Hold the typed contracts, ingestion, inference, replay, "
                "retrieval, drift, stewardship, and job surfaces in one tested service edge."
            ),
            directories=[
                "src/advanced_multimodal_ai/api.py",
                "src/advanced_multimodal_ai/service.py",
                "src/advanced_multimodal_ai/connectors.py",
                "src/advanced_multimodal_ai/pipelines.py",
                "src/advanced_multimodal_ai/stewardship_store.py",
                "src/advanced_multimodal_ai/benchmarks.py",
            ],
            entry_surfaces=[
                "/v1/infer",
                "/v1/connectors/pipeline-ingest",
                "/v1/pipelines/ingest",
                "/v1/research/surfaces",
                "/v1/benchmarks/reference",
            ],
            outputs=[
                "Typed API responses",
                "Persisted run records",
                "Connector benchmarks",
                "Research surface bundle",
                "Reference workload benchmark",
            ],
            proof_points=[
                "pytest covers API behavior directly through FastAPI TestClient.",
                "Runtime attestation and proof bundle are emitted from the same backend package.",
            ],
            why_it_exists=(
                "This is the working service lane. It carries operational state, "
                "review state, and exported evidence together."
            ),
        ),
        ArchitectureLane(
            lane_id="compiled_core",
            label="Compiled signal core",
            layer="compiled",
            purpose=(
                "Keep deterministic tensor signatures and transcript-led cut "
                "logic in a compiled lane that can be tested separately."
            ),
            directories=[
                "crates/multimodal-core",
                "src/advanced_multimodal_ai/rust_bridge.py",
            ],
            entry_surfaces=[
                "cargo test -p multimodal-core",
                "/v1/data/provenance",
                "/v1/video/cuts",
            ],
            outputs=[
                "Deterministic signatures",
                "Video cut proposals",
            ],
            proof_points=[
                "Cargo tests validate the compiled lane independently.",
                (
                    "Python runtime surfaces call through a narrow bridge "
                    "rather than reimplementing the logic."
                ),
            ],
            why_it_exists=(
                "Compiled primitives stay small and explicit so performance work "
                "does not blur into orchestration code."
            ),
        ),
        ArchitectureLane(
            lane_id="benchmark_evidence",
            label="Benchmark evidence lane",
            layer="evidence",
            purpose=(
                "Exercise connector ingest, profiling, provenance, batch work, recipe "
                "handoff, and proof export together through one repeatable workload."
            ),
            directories=[
                "src/advanced_multimodal_ai/benchmarks.py",
                "scripts/export_benchmark_surfaces.py",
                "proof/benchmark-surfaces.json",
                "proof/benchmark-surfaces.md",
            ],
            entry_surfaces=[
                "/v1/benchmarks/reference",
                "python3 scripts/export_benchmark_surfaces.py",
            ],
            outputs=[
                "reference benchmark JSON",
                "reference benchmark Markdown",
            ],
            proof_points=[
                (
                    "The benchmark walks real repository lanes rather than "
                    "timing an isolated helper."
                ),
                "The public site can hydrate directly from generated benchmark evidence.",
            ],
            why_it_exists=(
                "A benchmark becomes more persuasive when it proves the "
                "choreography between lanes, not only isolated speed."
            ),
        ),
        ArchitectureLane(
            lane_id="generated_clients",
            label="Generated client surfaces",
            layer="client",
            purpose=(
                "Freeze the public API contract into reusable Python and TypeScript "
                "clients instead of asking downstream users to hand-copy payload shapes."
            ),
            directories=[
                "openapi/openapi.json",
                "sdk/python",
                "sdk/typescript",
                "scripts/export_openapi.py",
                "scripts/generate_sdk_surfaces.py",
            ],
            entry_surfaces=[
                "python3 scripts/export_openapi.py",
                "python3 scripts/generate_sdk_surfaces.py",
                "npm run --prefix sdk/typescript check",
            ],
            outputs=[
                "Python client",
                "TypeScript client",
                "OpenAPI contract",
            ],
            proof_points=[
                "Generated clients are rebuilt from the live app contract.",
                "TypeScript compilation confirms the generated surface remains coherent.",
            ],
            why_it_exists=(
                "Client packaging belongs beside the contract it reflects, not "
                "in a separate storytelling lane."
            ),
        ),
        ArchitectureLane(
            lane_id="proof_exports",
            label="Proof and replay archive",
            layer="evidence",
            purpose=(
                "Publish runtime proof, readiness posture, worked examples, and "
                "research surfaces as exportable artifacts."
            ),
            directories=[
                "proof",
                "scripts/build_runtime_proof_bundle.py",
                "scripts/export_execution_journal.py",
                "scripts/export_readiness_report.py",
                "scripts/export_example_bundle.py",
                "scripts/export_research_surfaces.py",
            ],
            entry_surfaces=[
                "/v1/runtime/attestation",
                "/v1/proof/bundle",
                "/v1/readiness/report",
                "/v1/research/surfaces",
                "/v1/execution/journal",
            ],
            outputs=[
                "runtime-proof.json",
                "readiness-report.json",
                "example-bundle.json",
                "research-surfaces.json",
                "execution-journal.json",
            ],
            proof_points=[
                "Exports can be regenerated locally from the runtime.",
                "The static site reads the same evidence files that verification emits.",
                "Export and verification scripts now write their own journal receipts.",
            ],
            why_it_exists=(
                "A repository becomes easier to trust when proof can be "
                "regenerated, inspected, and linked back to running code."
            ),
        ),
    ]


def build_repository_findings(
    *,
    attestation: RuntimeAttestationResponse,
    proof_bundle: RuntimeProofBundle,
    readiness: ReadinessReport,
    model_cards: List[ModelResearchCard],
) -> List[RepositoryFinding]:
    runtime_ready_count = sum(1 for card in model_cards if card.runtime_ready)
    connector_run_count = attestation.store_counts.get("connector_runs", 0)
    policy_count = attestation.store_counts.get("lifecycle_policies", 0)
    change_count = attestation.store_counts.get("change_controls", 0)
    supply_count = attestation.store_counts.get("supply_chain_snapshots", 0)
    drift_count = attestation.store_counts.get("drift_baselines", 0)
    ontology_count = attestation.store_counts.get("ontology_snapshots", 0)
    pipeline_count = attestation.store_counts.get("pipeline_runs", 0)
    execution_journal_count = attestation.store_counts.get("execution_journal_runs", 0)

    findings: List[RepositoryFinding] = [
        RepositoryFinding(
            finding_id="connector-spine-is-real",
            lens="data",
            title=(
                "The repository now begins with measured intake instead of "
                "hand-shaped payloads alone"
            ),
            summary=(
                f"{connector_run_count} connector runs and "
                f"{len(proof_bundle.connector_kinds)} typed connector kinds "
                "mean the repo can start from rows, contracts, and public "
                "pages before tensor work begins."
            ),
            evidence=[
                f"connector runs recorded: {connector_run_count}",
                f"connector kinds exported: {', '.join(proof_bundle.connector_kinds)}",
            ],
            why_it_matters=(
                "A multimodal repository becomes more credible when data entry "
                "is a first-class engineering problem rather than an invisible "
                "notebook precondition."
            ),
            next_step=(
                "Broaden the evidence base with more repeated connector runs "
                "against non-trivial sources so the intake lane is tested "
                "under variation, not only under design-time examples."
            ),
            related_surfaces=[
                "/v1/connectors/register",
                "/v1/connectors/pipeline-ingest",
                "/v1/catalog/register",
            ],
            related_files=[
                "src/advanced_multimodal_ai/connectors.py",
                "src/advanced_multimodal_ai/catalog.py",
                "src/advanced_multimodal_ai/pipelines.py",
            ],
        ),
        RepositoryFinding(
            finding_id="review-lives-next-to-runtime",
            lens="governance",
            title="Review work now sits beside inference instead of after it",
            summary=(
                f"Lifecycle policies ({policy_count}), change controls "
                f"({change_count}), supply snapshots ({supply_count}), drift "
                f"baselines ({drift_count}), and ontology snapshots "
                f"({ontology_count}) are persisted in the same backend story."
            ),
            evidence=[
                f"lifecycle policies: {policy_count}",
                f"change controls: {change_count}",
                f"supply snapshots: {supply_count}",
                f"drift baselines: {drift_count}",
                f"ontology snapshots: {ontology_count}",
            ],
            why_it_matters=(
                "It is easier to trust a system when retention, movement, and "
                "liability have a code path rather than only a meeting note."
            ),
            next_step=(
                "Keep tying review surfaces to real route traces so the "
                "governance lane reflects operational movement, not just "
                "intended policy."
            ),
            related_surfaces=[
                "/v1/stewardship/posture",
                "/v1/drift/check",
                "/v1/ontology/liability",
            ],
            related_files=[
                "src/advanced_multimodal_ai/stewardship_store.py",
                "src/advanced_multimodal_ai/drift.py",
                "src/advanced_multimodal_ai/liability_surface.py",
            ],
        ),
        RepositoryFinding(
            finding_id="archive-and-runtime-are-distinct",
            lens="research",
            title="The research archive remains visible without pretending it is the whole runtime",
            summary=(
                f"{runtime_ready_count} of {len(model_cards)} listed models "
                "are runtime-ready in the current environment. That "
                "separation makes the repo more honest about what is live "
                "today and what still belongs to active study."
            ),
            evidence=[
                f"listed models: {len(model_cards)}",
                f"runtime-ready models: {runtime_ready_count}",
            ],
            why_it_matters=(
                "A public repository becomes easier to adopt when it is clear "
                "which layers are operational, which are archival, and how the "
                "two still inform each other."
            ),
            next_step=(
                "Add stronger benchmark evidence for the research archive so "
                "promotion into the runtime edge can be argued from results "
                "rather than enthusiasm."
            ),
            related_surfaces=["/v1/models", "/v1/research/models"],
            related_files=[
                "src/advanced_multimodal_ai/registry.py",
                "src/advanced_multimodal_ai/research_surfaces.py",
                "dynamic_transformer.py",
                "complete_model.py",
            ],
        ),
        RepositoryFinding(
            finding_id="proof-is-now-a-backend-surface",
            lens="evaluation",
            title="Proof is no longer only a README habit",
            summary=(
                f"The bundle currently counts {proof_bundle.route_count} "
                f"routes, {proof_bundle.test_count} tests, and "
                f"{proof_bundle.verification_artifact_count} declared "
                "artifacts."
            ),
            evidence=[
                f"route count: {proof_bundle.route_count}",
                f"test count: {proof_bundle.test_count}",
                f"verification artifacts: {proof_bundle.verification_artifact_count}",
                f"pipeline runs stored: {pipeline_count}",
            ],
            why_it_matters=(
                "Trust improves when proof is generated from code paths that "
                "actually exist and can be re-exported for the public site."
            ),
            next_step=(
                "Keep the export surfaces close to CI and extend replay "
                "comparisons so proof covers behavioral continuity, not only "
                "route and artifact presence."
            ),
            related_surfaces=[
                "/v1/proof/bundle",
                "/v1/runtime/attestation",
                "/v1/readiness/report",
            ],
            related_files=[
                "src/advanced_multimodal_ai/proof.py",
                "src/advanced_multimodal_ai/attestation.py",
                "scripts/export_readiness_report.py",
            ],
        ),
        RepositoryFinding(
            finding_id="execution-memory-is-persisted",
            lens="evaluation",
            title="Export and verification work now leaves its own operational memory",
            summary=(
                f"{execution_journal_count} persisted execution-journal runs "
                "now describe which proof and packaging lanes actually ran, "
                "what they touched, and when they last changed."
            ),
            evidence=[
                f"execution journal runs: {execution_journal_count}",
                "proof/execution-journal.json is exported from the backend journal surface.",
            ],
            why_it_matters=(
                "A repository feels more trustworthy when its export and "
                "verification lanes can be revisited as records instead of "
                "being remembered only because someone ran them recently."
            ),
            next_step=(
                "Keep letting new export and benchmark lanes write their own "
                "receipts so operational continuity becomes visible over time."
            ),
            related_surfaces=[
                "/v1/execution/journal",
                "/v1/repository/pulse",
            ],
            related_files=[
                "src/advanced_multimodal_ai/execution_journal.py",
                "src/advanced_multimodal_ai/execution_journal_store.py",
                "scripts/export_execution_journal.py",
            ],
        ),
        RepositoryFinding(
            finding_id="reference-benchmark-lane-is-repeatable",
            lens="evaluation",
            title="The benchmark lane now tests choreography, not just speed",
            summary=(
                "A typed reference workload now exercises connector-backed ingest, "
                "profiling, provenance, concurrent batch execution, recipe compilation, "
                "and proof export as one repeatable route."
            ),
            evidence=[
                "Reference benchmark surface: /v1/benchmarks/reference",
                "Generated artifact: proof/benchmark-surfaces.json",
                "Concurrent job evidence is persisted under the async job store.",
            ],
            why_it_matters=(
                "This shifts the repository away from isolated timing theatre "
                "and toward proof that multiple lanes can keep their story "
                "straight together."
            ),
            next_step=(
                "Keep widening the benchmark inputs with more "
                "warehouse-shaped and public-domain workloads so the same "
                "route is tested under broader operational texture."
            ),
            related_surfaces=[
                "/v1/benchmarks/reference",
                "/v1/jobs/batch-infer",
                "/v1/connectors/pipeline-ingest",
            ],
            related_files=[
                "src/advanced_multimodal_ai/benchmarks.py",
                "src/advanced_multimodal_ai/service.py",
                "scripts/export_benchmark_surfaces.py",
            ],
        ),
        RepositoryFinding(
            finding_id="what-still-needs-field-time",
            lens="runtime",
            title="The next gains will come from deeper field evidence, not louder claims",
            summary=(
                f"The current readiness posture is '{readiness.posture}'. The "
                "repo now has a steadier runtime edge, though the strongest "
                "next step remains more repeated evidence under varied real "
                "inputs."
            ),
            evidence=[
                f"readiness posture: {readiness.posture}",
                f"connector runs: {connector_run_count}",
                f"pipeline runs: {pipeline_count}",
                f"compiled recipes: {readiness.compiled_recipe_count}",
            ],
            why_it_matters=(
                "The repository is more valuable when it is explicit about "
                "what has been proven, what is promising, and what still needs "
                "to earn its place."
            ),
            next_step=(
                "Bring in more repeated warehouse, object-store, and "
                "mixed-modality examples so the runtime is exercised under "
                "broader operational texture."
            ),
            related_surfaces=[
                "/v1/readiness/report",
                "/v1/pipelines/runs/{run_id}/replay",
                "/v1/recipes/compile",
            ],
            related_files=[
                "src/advanced_multimodal_ai/readiness.py",
                "src/advanced_multimodal_ai/replay.py",
                "src/advanced_multimodal_ai/recipes.py",
            ],
        ),
    ]
    return findings


def build_research_surface_bundle(
    *,
    service_name: str,
    version: str,
    attestation: RuntimeAttestationResponse,
    proof_bundle: RuntimeProofBundle,
    readiness: ReadinessReport,
    registered_models: List[RegisteredModelResponse],
) -> ResearchSurfaceBundle:
    model_cards = build_model_research_cards(registered_models=registered_models)
    findings = build_repository_findings(
        attestation=attestation,
        proof_bundle=proof_bundle,
        readiness=readiness,
        model_cards=model_cards,
    )
    lanes = build_architecture_lanes()
    connections = build_repository_connections()
    open_question_count = sum(len(card.open_questions) for card in model_cards)
    runtime_ready_count = sum(1 for card in model_cards if card.runtime_ready)

    return ResearchSurfaceBundle(
        service=service_name,
        version=version,
        readiness_posture=readiness.posture,
        summary=ResearchSurfaceSummary(
            route_count=proof_bundle.route_count,
            test_count=proof_bundle.test_count,
            connector_kind_count=len(proof_bundle.connector_kinds),
            model_count=len(model_cards),
            runtime_ready_model_count=runtime_ready_count,
            open_question_count=open_question_count,
        ),
        lanes=lanes,
        model_cards=model_cards,
        findings=findings,
        connections=connections,
    )
