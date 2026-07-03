from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from statistics import median
from time import perf_counter
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import numpy as np

from .alignment import build_temporal_alignment
from .attestation import build_runtime_attestation
from .bias_taxonomy import assess_bias, list_bias_taxonomy
from .catalog import compare_dataset_schemas, register_dataset
from .catalog_store import CatalogStore
from .config import Settings
from .connector_store import ConnectorStore
from .connectors import (
    build_pipeline_events_from_rows,
    connector_source_domain,
    infer_dataset_fields,
    materialize_connector_rows,
)
from .contracts import (
    AsyncJobRecord,
    AsyncJobSubmissionResponse,
    BatchInferenceRequest,
    BenchmarkResult,
    BiasAssessmentRequest,
    BiasAssessmentResponse,
    BiasCategory,
    ChangeControlRecord,
    ChangeControlRequest,
    ConnectorPipelineIngestRequest,
    ConnectorPipelineIngestResponse,
    ConnectorRegistrationRequest,
    ConnectorRegistrationResponse,
    ConnectorRunRecord,
    DataLifecyclePolicyRecord,
    DataLifecyclePolicyRequest,
    DataProfileResponse,
    DatasetEvolutionRequest,
    DatasetEvolutionResponse,
    DatasetRecord,
    DatasetRegistrationRequest,
    DriftBaselineRecord,
    DriftBaselineRequest,
    HealthResponse,
    InferenceRequest,
    InferenceResponse,
    LiabilitySurfaceResponse,
    LiabilitySurfacingRequest,
    OntologyIngestRequest,
    OntologySnapshot,
    OutputSummary,
    PipelineIngestRequest,
    PipelineReplayResponse,
    PipelineRunExport,
    PipelineRunRecord,
    PopulationDriftRequest,
    PopulationDriftResponse,
    ProvenanceReceipt,
    ReadinessReport,
    RecipeCompileRequest,
    RecipeRecord,
    RetrievalQueryRequest,
    RetrievalQueryResponse,
    RetrievalUpsertRequest,
    RuntimeAttestationResponse,
    RuntimeProofBundle,
    StewardshipCoverageItem,
    StewardshipPostureResponse,
    SuggestedCut,
    SupplyChainSnapshotRecord,
    SupplyChainSnapshotRequest,
    TemporalAlignmentRequest,
    TemporalAlignmentResponse,
    TimeSpan,
    VideoCleaningRequest,
    VideoCleaningResponse,
    VideoPacketRequest,
    VideoPacketResponse,
)
from .domain_ontology import ingest_domain_ontology
from .drift import assess_population_drift, create_drift_baseline_record
from .drift_store import DriftStore
from .job_store import JobStore
from .legacy import RESEARCH_MODELS
from .liability_surface import surface_operational_liability
from .observability import observe_inference, record_data_plane, record_retrieval
from .ontology_store import OntologyStore
from .orchestration import build_inference_plan
from .pipeline_store import PipelineStore
from .pipelines import build_inference_request_from_pipeline
from .proof import build_runtime_proof_bundle
from .provenance import build_provenance_receipt
from .quality import build_data_profile
from .readiness import build_readiness_report
from .recipe_store import RecipeStore
from .recipes import compile_recipe_record
from .registry import list_registered_models
from .replay import compare_replay, export_pipeline_run
from .retrieval import create_vector_index
from .rust_bridge import signature_from_payload, video_cuts_from_payload
from .signal_math import arrays_from_request, output_summary, signature
from .stewardship_store import StewardshipStore
from .video import build_video_cleaning_response, build_video_packet

try:
    import torch
except Exception:  # pragma: no cover - optional dependency path
    torch = None


class PopulationDriftBlockedError(RuntimeError):
    def __init__(self, response: PopulationDriftResponse) -> None:
        super().__init__("population drift gate blocked inference")
        self.response = response


def _softmax(values: np.ndarray) -> np.ndarray:
    shifted = values - np.max(values, axis=-1, keepdims=True)
    exp_values = np.exp(shifted)
    return exp_values / exp_values.sum(axis=-1, keepdims=True)


def _metadata_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _classification_surface(
    embedding: np.ndarray, num_classes: int
) -> Tuple[np.ndarray, np.ndarray]:
    feature_width = embedding.shape[1]
    basis = np.vstack(
        [
            np.cos(np.linspace(0.0, math.pi * (class_index + 1), feature_width))
            for class_index in range(num_classes)
        ]
    ).astype(np.float32)
    logits = embedding @ basis.T
    probabilities = _softmax(logits)
    return logits, probabilities


def _parse_utc_timestamp(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _serialize_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


class AdvancedMultimodalService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.vector_index = create_vector_index(self.settings)
        self.job_store = JobStore(self.settings.async_job_db_path)
        self.catalog_store = CatalogStore(self.settings.dataset_catalog_db_path)
        self.connector_store = ConnectorStore(self.settings.connector_db_path)
        self.drift_store = DriftStore(self.settings.drift_baseline_db_path)
        self.pipeline_store = PipelineStore(self.settings.pipeline_run_db_path)
        self.ontology_store = OntologyStore(self.settings.ontology_db_path)
        self.recipe_store = RecipeStore(self.settings.recipe_db_path)
        self.stewardship_store = StewardshipStore(self.settings.stewardship_db_path)

    @property
    def torch_available(self) -> bool:
        return torch is not None

    def health(self) -> HealthResponse:
        status = "ok"
        if (
            self.settings.retrieval_backend.lower() == "qdrant"
            and self.vector_index.backend != "qdrant"
        ):
            status = "degraded"
        return HealthResponse(
            service=self.settings.service_name,
            version=self.settings.service_version,
            environment=self.settings.environment,
            status=status,
            torch_available=self.torch_available,
            metrics_enabled=self.settings.enable_metrics,
        )

    def list_models(self):
        return list_registered_models(torch_available=self.torch_available)

    def list_bias_taxonomy(self) -> List[BiasCategory]:
        record_data_plane("bias_taxonomy")
        return list_bias_taxonomy()

    def assess_bias(self, request: BiasAssessmentRequest) -> BiasAssessmentResponse:
        record_data_plane("bias_assessment")
        return assess_bias(request)

    def register_dataset(self, request: DatasetRegistrationRequest) -> DatasetRecord:
        record_data_plane("dataset_catalog_register")
        record = register_dataset(request, self.settings)
        return self.catalog_store.save_dataset(record)

    def list_datasets(self, limit: int = 100) -> List[DatasetRecord]:
        record_data_plane("dataset_catalog_list")
        return self.catalog_store.list_datasets(limit=limit)

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        return self.catalog_store.get_dataset(dataset_id)

    def compare_dataset_evolution(
        self, request: DatasetEvolutionRequest
    ) -> DatasetEvolutionResponse:
        record_data_plane("dataset_catalog_evolution")
        current = self.catalog_store.get_latest_by_name(request.dataset_name)
        if current is None:
            raise ValueError(
                f"Dataset '{request.dataset_name}' has not been registered yet"
            )
        return compare_dataset_schemas(current, request)

    def register_lifecycle_policy(
        self, request: DataLifecyclePolicyRequest
    ) -> DataLifecyclePolicyRecord:
        record_data_plane("stewardship_lifecycle_register")
        dataset = self.catalog_store.get_latest_by_name(request.dataset_name)
        if dataset is None:
            raise ValueError(
                f"Dataset '{request.dataset_name}' must be registered before a lifecycle policy."
            )

        effective_from = _parse_utc_timestamp(request.effective_from)
        half_life_at = effective_from + timedelta(days=request.half_life_days)
        next_review_at = effective_from + timedelta(days=request.review_interval_days)
        removal_due_at = effective_from + timedelta(days=request.retention_days)
        now = datetime.now(timezone.utc)

        if removal_due_at <= now:
            state = "removal_due"
        elif next_review_at <= now:
            state = "review_due"
        else:
            state = "active"

        notes = list(request.notes)
        if half_life_at <= now:
            notes.append("This policy has already crossed its declared data half-life.")
        if state == "removal_due":
            notes.append("The declared retention window has already elapsed.")

        record = DataLifecyclePolicyRecord(
            dataset_id=dataset.dataset_id,
            dataset_name=dataset.dataset_name,
            dataset_version=dataset.version,
            owner=request.owner,
            data_classification=request.data_classification,
            residency_regions=request.residency_regions,
            allowed_uses=request.allowed_uses,
            effective_from=_serialize_utc_timestamp(effective_from),
            retention_days=request.retention_days,
            half_life_days=request.half_life_days,
            review_interval_days=request.review_interval_days,
            half_life_at=_serialize_utc_timestamp(half_life_at),
            next_review_at=_serialize_utc_timestamp(next_review_at),
            removal_due_at=_serialize_utc_timestamp(removal_due_at),
            removal_mode=request.removal_mode,
            deletion_evidence_required=request.deletion_evidence_required,
            state=state,
            evidence_refs=request.evidence_refs,
            notes=notes,
        )
        return self.stewardship_store.save_lifecycle_policy(record)

    def list_lifecycle_policies(self, limit: int = 100) -> List[DataLifecyclePolicyRecord]:
        record_data_plane("stewardship_lifecycle_list")
        return self.stewardship_store.list_lifecycle_policies(limit=limit)

    def get_lifecycle_policy(self, policy_id: str) -> DataLifecyclePolicyRecord | None:
        return self.stewardship_store.get_lifecycle_policy(policy_id)

    def create_change_control(self, request: ChangeControlRequest) -> ChangeControlRecord:
        record_data_plane("stewardship_change_control_create")
        for dataset_name in request.affected_datasets:
            if self.catalog_store.get_latest_by_name(dataset_name) is None:
                raise ValueError(
                    "Dataset "
                    f"'{dataset_name}' must be registered before it can appear "
                    "in change control."
                )
        for policy_id in request.linked_policy_ids:
            if self.stewardship_store.get_lifecycle_policy(policy_id) is None:
                raise ValueError(
                    f"Lifecycle policy '{policy_id}' must exist before it can be linked."
                )

        record = ChangeControlRecord(
            title=request.title,
            owner=request.owner,
            change_kind=request.change_kind,
            severity=request.severity,
            status=request.status,
            summary=request.summary,
            affected_datasets=request.affected_datasets,
            affected_connectors=request.affected_connectors,
            affected_routes=request.affected_routes,
            linked_policy_ids=request.linked_policy_ids,
            planned_window=request.planned_window,
            validation_commands=request.validation_commands,
            rollback_notes=request.rollback_notes,
            evidence_refs=request.evidence_refs,
            notes=request.notes,
        )
        return self.stewardship_store.save_change_control(record)

    def list_change_controls(self, limit: int = 100) -> List[ChangeControlRecord]:
        record_data_plane("stewardship_change_control_list")
        return self.stewardship_store.list_change_controls(limit=limit)

    def get_change_control(self, change_id: str) -> ChangeControlRecord | None:
        return self.stewardship_store.get_change_control(change_id)

    def create_supply_chain_snapshot(
        self, request: SupplyChainSnapshotRequest
    ) -> SupplyChainSnapshotRecord:
        record_data_plane("stewardship_supply_chain_create")
        node_ids = {node.node_id for node in request.nodes}
        for node in request.nodes:
            if (
                node.dataset_name
                and self.catalog_store.get_latest_by_name(node.dataset_name) is None
            ):
                raise ValueError(
                    "Dataset "
                    f"'{node.dataset_name}' must be registered before it can appear "
                    "in the supply chain."
                )
        for edge in request.edges:
            if edge.from_node_id not in node_ids or edge.to_node_id not in node_ids:
                raise ValueError(
                    "Supply chain edges must point to nodes declared in the same snapshot."
                )

        cross_border_edge_count = sum(1 for edge in request.edges if edge.cross_border)
        governed_edge_count = sum(1 for edge in request.edges if edge.governed)
        ungoverned_edge_count = sum(1 for edge in request.edges if not edge.governed)
        deletion_ready_edge_count = sum(1 for edge in request.edges if edge.deletion_supported)
        notes = list(request.notes)
        if ungoverned_edge_count:
            notes.append(
                f"{ungoverned_edge_count} supply edges still move without an explicit control."
            )

        record = SupplyChainSnapshotRecord(
            label=request.label,
            owner=request.owner,
            tenant_id=request.tenant_id,
            node_count=len(request.nodes),
            edge_count=len(request.edges),
            cross_border_edge_count=cross_border_edge_count,
            governed_edge_count=governed_edge_count,
            ungoverned_edge_count=ungoverned_edge_count,
            deletion_ready_edge_count=deletion_ready_edge_count,
            nodes=request.nodes,
            edges=request.edges,
            evidence_refs=request.evidence_refs,
            notes=notes,
        )
        return self.stewardship_store.save_supply_chain_snapshot(record)

    def list_supply_chain_snapshots(self, limit: int = 100) -> List[SupplyChainSnapshotRecord]:
        record_data_plane("stewardship_supply_chain_list")
        return self.stewardship_store.list_supply_chain_snapshots(limit=limit)

    def get_supply_chain_snapshot(
        self, snapshot_id: str
    ) -> SupplyChainSnapshotRecord | None:
        return self.stewardship_store.get_supply_chain_snapshot(snapshot_id)

    def stewardship_posture(self) -> StewardshipPostureResponse:
        record_data_plane("stewardship_posture")
        datasets = self.catalog_store.list_datasets(limit=1000)
        change_controls = self.stewardship_store.list_change_controls(limit=1000)
        supply_snapshots = self.stewardship_store.list_supply_chain_snapshots(limit=1000)
        now = datetime.now(timezone.utc)

        coverage_items: List[StewardshipCoverageItem] = []
        warnings: List[str] = []
        covered_dataset_count = 0

        for dataset in datasets:
            policy = self.stewardship_store.get_latest_lifecycle_for_dataset(
                dataset.dataset_name
            )
            review_due = False
            removal_due = False
            if policy is not None:
                covered_dataset_count += 1
                review_due = _parse_utc_timestamp(policy.next_review_at) <= now
                removal_due = _parse_utc_timestamp(policy.removal_due_at) <= now
            else:
                warnings.append(
                    f"{dataset.dataset_name} does not yet have a persisted lifecycle policy."
                )

            coverage_items.append(
                StewardshipCoverageItem(
                    dataset_id=dataset.dataset_id,
                    dataset_name=dataset.dataset_name,
                    dataset_version=dataset.version,
                    has_policy=policy is not None,
                    policy_id=policy.policy_id if policy is not None else "",
                    data_classification=policy.data_classification if policy is not None else "",
                    review_due=review_due,
                    removal_due=removal_due,
                    next_review_at=policy.next_review_at if policy is not None else "",
                    half_life_at=policy.half_life_at if policy is not None else "",
                    removal_due_at=policy.removal_due_at if policy is not None else "",
                    notes=policy.notes if policy is not None else [],
                )
            )

        cross_border_edge_count = sum(
            snapshot.cross_border_edge_count for snapshot in supply_snapshots
        )
        ungoverned_edge_count = sum(
            snapshot.ungoverned_edge_count for snapshot in supply_snapshots
        )
        deletion_ready_edge_count = sum(
            snapshot.deletion_ready_edge_count for snapshot in supply_snapshots
        )

        if not supply_snapshots:
            warnings.append("No supply-chain snapshot has been recorded yet.")
        if not change_controls:
            warnings.append("No change-control register has been recorded yet.")

        return StewardshipPostureResponse(
            dataset_count=len(datasets),
            policy_count=self.stewardship_store.count_lifecycle_policies(),
            covered_dataset_count=covered_dataset_count,
            uncovered_dataset_count=max(len(datasets) - covered_dataset_count, 0),
            open_change_controls=sum(
                1 for item in change_controls if item.status in {"proposed", "approved"}
            ),
            approved_change_controls=sum(
                1 for item in change_controls if item.status == "approved"
            ),
            supply_chain_snapshot_count=len(supply_snapshots),
            cross_border_edge_count=cross_border_edge_count,
            ungoverned_edge_count=ungoverned_edge_count,
            deletion_ready_edge_count=deletion_ready_edge_count,
            datasets=coverage_items,
            warnings=warnings,
        )

    def register_connector_dataset(
        self, request: ConnectorRegistrationRequest
    ) -> ConnectorRegistrationResponse:
        record_data_plane("connector_register")
        prior_web_receipt = None
        if request.connector.kind == "web_html":
            prior_web_receipt = self.connector_store.get_latest_web_receipt(
                connector_source_domain(request.connector.source)
            )
        materialized = materialize_connector_rows(
            request.connector,
            request.limit,
            prior_web_receipt=prior_web_receipt,
        )
        rows = materialized.rows
        benchmark = materialized.benchmark
        fields = infer_dataset_fields(rows)
        dataset_record = self.catalog_store.save_dataset(
            register_dataset(
                DatasetRegistrationRequest(
                    dataset_name=request.dataset_name,
                    owner=request.owner,
                    version=request.version,
                    modality=request.modality,
                    partition_keys=request.partition_keys,
                    primary_keys=request.primary_keys,
                    fields=fields,
                    tags=request.tags,
                    notes=request.notes,
                ),
                self.settings,
            )
        )
        connector_run = ConnectorRunRecord(
            connector_kind=request.connector.kind,
            source=request.connector.source,
            dataset_name=request.dataset_name,
            record_count=len(rows),
            dropped_rows=0,
            benchmark=benchmark,
            dataset_id=dataset_record.dataset_id,
            web_receipt=materialized.web_receipt,
            notes=["dataset contract registered from connector rows"],
        )
        self.connector_store.save_run(connector_run)
        return ConnectorRegistrationResponse(
            dataset=dataset_record,
            benchmark=benchmark,
            record_count=len(rows),
            sample_rows=rows[: request.sample_size],
        )

    def connector_pipeline_ingest(
        self, request: ConnectorPipelineIngestRequest
    ) -> ConnectorPipelineIngestResponse:
        record_data_plane("connector_pipeline_ingest")
        prior_web_receipt = None
        if request.connector.kind == "web_html":
            prior_web_receipt = self.connector_store.get_latest_web_receipt(
                connector_source_domain(request.connector.source)
            )
        materialized = materialize_connector_rows(
            request.connector,
            request.limit,
            prior_web_receipt=prior_web_receipt,
        )
        rows = materialized.rows
        benchmark = materialized.benchmark
        fields = infer_dataset_fields(rows)
        dataset_record = self.catalog_store.save_dataset(
            register_dataset(
                DatasetRegistrationRequest(
                    dataset_name=request.dataset_name,
                    owner=request.owner,
                    version=request.version,
                    modality="tabular",
                    partition_keys=request.partition_keys,
                    primary_keys=request.primary_keys,
                    fields=fields,
                    tags=request.tags,
                    notes=request.notes,
                ),
                self.settings,
            )
        )
        events, dropped_rows = build_pipeline_events_from_rows(
            rows=rows,
            mappings=request.modality_mappings,
            partition_key_field=request.partition_key_field,
            drop_invalid_rows=request.drop_invalid_rows,
        )
        if not events:
            raise ValueError("Connector rows did not yield any valid pipeline events")
        pipeline_run = self.ingest_pipeline_batch(
            PipelineIngestRequest(
                stream_id=request.stream_id,
                batch_label=request.batch_label,
                model_id=request.model_id,
                runtime_mode=request.runtime_mode,
                target=request.target,
                num_classes=request.num_classes,
                baseline_label=request.baseline_label,
                block_population_drift=request.block_population_drift,
                notes=[
                    *request.notes,
                    f"connector source: {request.connector.source}",
                    f"connector kind: {request.connector.kind}",
                    f"connector dropped rows: {dropped_rows}",
                ],
                events=events,
            )
        )
        connector_run = self.connector_store.save_run(
            ConnectorRunRecord(
                connector_kind=request.connector.kind,
                source=request.connector.source,
                dataset_name=request.dataset_name,
                record_count=len(rows),
                dropped_rows=dropped_rows,
                benchmark=benchmark,
                dataset_id=dataset_record.dataset_id,
                pipeline_run_id=pipeline_run.run_id,
                web_receipt=materialized.web_receipt,
                notes=[
                    f"sample rows returned: {min(len(rows), request.sample_size)}",
                    f"pipeline events created: {len(events)}",
                ],
            )
        )
        return ConnectorPipelineIngestResponse(
            connector_run=connector_run,
            dataset=dataset_record,
            pipeline_run=pipeline_run,
        )

    def get_connector_run(self, run_id: str) -> ConnectorRunRecord | None:
        return self.connector_store.get_run(run_id)

    def list_connector_runs(self, limit: int = 50) -> List[ConnectorRunRecord]:
        record_data_plane("connector_list")
        return self.connector_store.list_runs(limit=limit)

    def runtime_attestation(self) -> RuntimeAttestationResponse:
        record_data_plane("runtime_attestation")
        return build_runtime_attestation(
            settings=self.settings,
            store_counts={
                "async_jobs": self.job_store.count_jobs(),
                "dataset_catalog": self.catalog_store.count_datasets(),
                "connector_runs": self.connector_store.count_runs(),
                "drift_baselines": self.drift_store.count_baselines(),
                "pipeline_runs": self.pipeline_store.count_runs(),
                "ontology_snapshots": self.ontology_store.count_snapshots(),
                "recipe_registry": self.recipe_store.count_recipes(),
                "lifecycle_policies": self.stewardship_store.count_lifecycle_policies(),
                "change_controls": self.stewardship_store.count_change_controls(),
                "supply_chain_snapshots": (
                    self.stewardship_store.count_supply_chain_snapshots()
                ),
            },
        )

    def runtime_proof_bundle(self, route_count: int) -> RuntimeProofBundle:
        record_data_plane("runtime_proof_bundle")
        return build_runtime_proof_bundle(
            attestation=self.runtime_attestation(),
            route_count=route_count,
        )

    def readiness_report(self, route_count: int) -> ReadinessReport:
        record_data_plane("readiness_report")
        attestation = self.runtime_attestation()
        proof_bundle = build_runtime_proof_bundle(
            attestation=attestation,
            route_count=route_count,
        )
        recipes = self.recipe_store.list_recipes(limit=1000)
        return build_readiness_report(
            attestation=attestation,
            proof_bundle=proof_bundle,
            recipes=recipes,
        )

    def plan(self, request: InferenceRequest):
        return build_inference_plan(request)

    def compile_recipe(self, request: RecipeCompileRequest) -> RecipeRecord:
        record_data_plane("recipe_compile")
        record = compile_recipe_record(
            request,
            catalog_store=self.catalog_store,
        )
        return self.recipe_store.save_recipe(record)

    def list_recipes(self, limit: int = 100) -> List[RecipeRecord]:
        record_data_plane("recipe_list")
        return self.recipe_store.list_recipes(limit=limit)

    def get_recipe(self, recipe_id: str) -> RecipeRecord | None:
        return self.recipe_store.get_recipe(recipe_id)

    def profile_request(self, request: InferenceRequest) -> DataProfileResponse:
        record_data_plane("profile")
        return build_data_profile(request)

    def build_provenance(self, request: InferenceRequest) -> ProvenanceReceipt:
        record_data_plane("provenance")
        return build_provenance_receipt(request)

    def align_temporal_observations(
        self, request: TemporalAlignmentRequest
    ) -> TemporalAlignmentResponse:
        record_data_plane("alignment")
        return build_temporal_alignment(request)

    def create_drift_baseline(self, request: DriftBaselineRequest) -> DriftBaselineRecord:
        record_data_plane("drift_baseline")
        profile = build_data_profile(request.request)
        record = create_drift_baseline_record(request, profile)
        return self.drift_store.save_baseline(record)

    def list_drift_baselines(self, limit: int = 50) -> List[DriftBaselineRecord]:
        record_data_plane("drift_baseline_list")
        return self.drift_store.list_baselines(limit=limit)

    def check_population_drift(
        self, request: PopulationDriftRequest
    ) -> PopulationDriftResponse:
        record_data_plane("drift_check")
        baseline = self.drift_store.get_baseline(request.baseline_label)
        if baseline is None:
            raise ValueError(f"Drift baseline '{request.baseline_label}' was not found")
        profile = build_data_profile(request.request)
        return assess_population_drift(baseline=baseline, current_profile=profile, request=request)

    def ingest_pipeline_batch(self, request: PipelineIngestRequest) -> PipelineRunRecord:
        record_data_plane("pipeline_ingest")
        inference_request, modality_counts, dropped_events = (
            build_inference_request_from_pipeline(request)
        )
        profile = build_data_profile(inference_request)
        provenance = build_provenance_receipt(inference_request)
        notes = list(request.notes)
        if dropped_events:
            notes.append(
                f"{dropped_events} events were held out because the modalities "
                "were paired to the narrowest shared batch."
            )

        drift_result: PopulationDriftResponse | None = None
        status = "accepted"
        inference_response: InferenceResponse | None = None

        if request.baseline_label:
            drift_result = self.check_population_drift(
                PopulationDriftRequest(
                    baseline_label=request.baseline_label,
                    request=inference_request,
                    block_on_failure=request.block_population_drift,
                )
            )
            if drift_result.blocked:
                status = "blocked"
                notes.append(
                    "The prepared population gate held this batch out before inference."
                )

        if status == "accepted":
            inference_response = self.infer(inference_request)

        record = PipelineRunRecord(
            stream_id=request.stream_id,
            batch_label=request.batch_label,
            status=status,
            model_id=request.model_id,
            runtime_mode=request.runtime_mode,
            target=request.target,
            event_count=len(request.events),
            paired_batch_size=int(inference_request.metadata["paired_batch_size"]),
            dropped_events=dropped_events,
            modality_counts=modality_counts,
            baseline_label=request.baseline_label,
            request_snapshot=inference_request,
            event_lineage=request.events,
            profile=profile,
            provenance=provenance,
            drift=drift_result,
            inference=inference_response,
            notes=notes,
        )
        return self.pipeline_store.save_run(record)

    def get_pipeline_run(self, run_id: str) -> PipelineRunRecord | None:
        return self.pipeline_store.get_run(run_id)

    def list_pipeline_runs(self, limit: int = 50) -> List[PipelineRunRecord]:
        record_data_plane("pipeline_list")
        return self.pipeline_store.list_runs(limit=limit)

    def export_pipeline_run(self, run_id: str) -> PipelineRunExport | None:
        record = self.pipeline_store.get_run(run_id)
        if record is None:
            return None
        record_data_plane("pipeline_export")
        return export_pipeline_run(record)

    def replay_pipeline_run(self, run_id: str) -> PipelineReplayResponse | None:
        record = self.pipeline_store.get_run(run_id)
        if record is None or record.request_snapshot is None:
            return None
        record_data_plane("pipeline_replay")
        replay_response = self.infer(record.request_snapshot)
        replay_provenance = build_provenance_receipt(record.request_snapshot)
        return compare_replay(
            record=record,
            replay_response=replay_response,
            replay_provenance_digest=replay_provenance.payload_digest,
        )

    def ingest_ontology(self, request: OntologyIngestRequest) -> OntologySnapshot:
        record_data_plane("ontology_ingest")
        snapshot = ingest_domain_ontology(request)
        return self.ontology_store.save_snapshot(snapshot)

    def get_ontology_snapshot(self, snapshot_id: str) -> OntologySnapshot | None:
        return self.ontology_store.get_snapshot(snapshot_id)

    def list_ontology_snapshots(self, limit: int = 50) -> List[OntologySnapshot]:
        record_data_plane("ontology_list")
        return self.ontology_store.list_snapshots(limit=limit)

    def surface_liability(
        self, request: LiabilitySurfacingRequest
    ) -> LiabilitySurfaceResponse:
        record_data_plane("ontology_liability")
        snapshot = self.ontology_store.get_snapshot(request.snapshot_id)
        if snapshot is None:
            raise ValueError(f"Ontology snapshot '{request.snapshot_id}' was not found")
        return surface_operational_liability(snapshot=snapshot, traces=request.traces)

    def submit_video_clean_job(
        self, request: VideoCleaningRequest
    ) -> AsyncJobSubmissionResponse:
        return self.job_store.create_job(
            kind="video_clean",
            request_payload=request.model_dump(mode="json"),
            record_count=1,
        )

    def run_video_clean_job(self, job_id: str, request: VideoCleaningRequest) -> None:
        self.job_store.mark_running(job_id)
        try:
            result = self.clean_video_packet(request)
            self.job_store.mark_completed(job_id, result.model_dump(mode="json"))
        except Exception as error:  # pragma: no cover - defensive async lane
            self.job_store.mark_failed(job_id, str(error))

    def submit_batch_inference_job(
        self, request: BatchInferenceRequest
    ) -> AsyncJobSubmissionResponse:
        return self.job_store.create_job(
            kind="batch_infer",
            request_payload=request.model_dump(mode="json"),
            record_count=len(request.requests),
        )

    def run_batch_inference_job(self, job_id: str, request: BatchInferenceRequest) -> None:
        self.job_store.mark_running(job_id)
        try:
            results = [self.infer(item).model_dump(mode="json") for item in request.requests]
            self.job_store.mark_completed(
                job_id,
                {
                    "label": request.label,
                    "record_count": len(results),
                    "results": results,
                },
            )
        except Exception as error:  # pragma: no cover - defensive async lane
            self.job_store.mark_failed(job_id, str(error))

    def get_job(self, job_id: str) -> AsyncJobRecord | None:
        return self.job_store.get_job(job_id)

    def list_jobs(self, limit: int = 20) -> List[AsyncJobRecord]:
        return self.job_store.list_jobs(limit=limit)

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        drift_result = self._maybe_run_population_drift_gate(request)
        drift_warnings = self._drift_warnings(drift_result) if drift_result is not None else []
        with observe_inference(request.runtime_mode, request.model_id):
            if request.runtime_mode == "research":
                research_result = self._try_research_inference(request)
                if research_result is not None:
                    if drift_warnings:
                        research_result.warnings = drift_warnings + research_result.warnings
                    return research_result
            response = self._contract_inference(
                request,
                fallback_from_research=request.runtime_mode == "research",
            )
            if drift_warnings:
                response.warnings = drift_warnings + response.warnings
            return response

    def upsert_retrieval_records(self, request: RetrievalUpsertRequest) -> Dict[str, Any]:
        written = self.vector_index.upsert(request)
        return {"written": written, "backend": self.vector_index.backend}

    def query_retrieval(self, request: RetrievalQueryRequest) -> RetrievalQueryResponse:
        record_retrieval(self.vector_index.backend)
        matches = self.vector_index.query(request)
        return RetrievalQueryResponse(matches=matches, backend=self.vector_index.backend)

    def build_video_packet(self, request: VideoPacketRequest) -> VideoPacketResponse:
        return build_video_packet(request)

    def clean_video_packet(self, request: VideoCleaningRequest) -> VideoCleaningResponse:
        bridge_payload = {
            "duration_ms": request.duration_ms,
            "transcript": [token.model_dump() for token in request.transcript],
            "silence_threshold_ms": request.silence_threshold_ms,
            "filler_words": request.filler_words,
            "max_cut_ms": request.max_cut_ms,
        }
        bridge_response = video_cuts_from_payload(bridge_payload, self.settings)
        if bridge_response is not None:
            removed_spans = [
                SuggestedCut.model_validate(span)
                for span in bridge_response.get("removed_spans", [])
            ]
            retained_spans = [
                TimeSpan.model_validate(span)
                for span in bridge_response.get("retained_spans", [])
            ]
            removed_duration_ms = sum(span.end_ms - span.start_ms for span in removed_spans)
            kept_duration_ms = sum(span.end_ms - span.start_ms for span in retained_spans)
            cut_script = [
                f"cut {span.start_ms}ms->{span.end_ms}ms [{span.reason}]"
                for span in removed_spans
            ]
            return VideoCleaningResponse(
                clip_id=request.clip_id,
                removed_spans=removed_spans,
                retained_spans=retained_spans,
                kept_duration_ms=kept_duration_ms,
                removed_duration_ms=removed_duration_ms,
                cut_script=cut_script,
                notes=[
                    "The Rust core generated these proposed cuts from "
                    "transcript timing and cleanup thresholds.",
                ],
            )
        return build_video_cleaning_response(request)

    def run_smoke_benchmark(self, model_id: str, iterations: int = 10) -> BenchmarkResult:
        latencies: List[float] = []
        request = self._benchmark_request(model_id=model_id)
        for _ in range(iterations):
            started = perf_counter()
            self._contract_inference(request, fallback_from_research=False)
            latencies.append((perf_counter() - started) * 1000)
        ordered = sorted(latencies)
        p95_index = max(int(len(ordered) * 0.95) - 1, 0)
        return BenchmarkResult(
            benchmark_id=str(uuid4()),
            runtime_mode="contract",
            model_id=model_id,
            iterations=iterations,
            median_latency_ms=float(median(ordered)),
            p95_latency_ms=float(ordered[p95_index]),
            notes="Deterministic smoke benchmark using fixed tensor fixtures.",
        )

    def _maybe_run_population_drift_gate(
        self, request: InferenceRequest
    ) -> PopulationDriftResponse | None:
        baseline_label = str(request.metadata.get("population_baseline_label", "")).strip()
        if not baseline_label:
            return None

        drift_request = PopulationDriftRequest(
            baseline_label=baseline_label,
            request=request,
            max_entropy_shift=float(request.metadata.get("max_entropy_shift", 0.25)),
            max_zero_shift=float(request.metadata.get("max_zero_shift", 0.25)),
            min_finite_ratio=float(request.metadata.get("min_finite_ratio", 0.98)),
            max_alignment_drop=float(request.metadata.get("max_alignment_drop", 0.35)),
            block_on_failure=_metadata_bool(
                request.metadata.get("block_population_drift"),
                True,
            ),
        )
        result = self.check_population_drift(drift_request)
        if result.blocked:
            raise PopulationDriftBlockedError(result)
        return result

    def _drift_warnings(
        self, result: PopulationDriftResponse | None
    ) -> List[str]:
        if result is None:
            return []
        warnings = list(result.warnings)
        warnings.append(
            "Population baseline "
            f"{result.baseline_label} drift score: {result.drift_score:.3f}."
        )
        return warnings

    def _contract_inference(
        self, request: InferenceRequest, fallback_from_research: bool = False
    ) -> InferenceResponse:
        arrays = arrays_from_request(request)
        signatures: Dict[str, np.ndarray] = {}
        summaries: Dict[str, OutputSummary] = {}

        for modality, payload in request.modalities.items():
            bridge_response = signature_from_payload(payload.model_dump(), self.settings)
            if bridge_response is not None:
                signatures[modality] = np.asarray(
                    bridge_response.get("signature", []), dtype=np.float32
                )
                summaries[modality] = OutputSummary.model_validate(
                    bridge_response["summary"]
                )
                continue
            array = arrays[modality]
            signatures[modality] = signature(array)
            summaries[modality] = output_summary(array)

        fused_embedding = np.mean(np.stack(list(signatures.values()), axis=0), axis=0)
        summaries["fused_embedding"] = output_summary(fused_embedding)

        outputs: Dict[str, Any] = {
            "modality_embeddings": {key: value.tolist() for key, value in signatures.items()},
            "fused_embedding": fused_embedding.tolist(),
        }
        warnings: List[str] = []
        if fallback_from_research:
            warnings.append(
                "Research mode was requested, but the contract lane handled "
                "this request because the research runtime is not ready in "
                "the current environment."
            )
        if request.target == "classification":
            num_classes = request.num_classes or 4
            logits, probabilities = _classification_surface(fused_embedding, num_classes)
            outputs["class_logits"] = logits.tolist()
            outputs["class_probabilities"] = probabilities.tolist()
            outputs["predicted_index"] = probabilities.argmax(axis=1).tolist()
        elif request.target == "translation":
            warnings.append(
                "Translation currently returns aligned multimodal signatures "
                "instead of generated natural-language or media output."
            )

        plan = self.plan(request)
        return InferenceResponse(
            model_id=request.model_id,
            runtime_mode="contract",
            route=[step.name for step in plan.steps],
            outputs=outputs,
            summaries=summaries,
            warnings=warnings,
        )

    def stream_inference_events(self, request: InferenceRequest) -> List[Dict[str, Any]]:
        plan = self.plan(request)
        response = self.infer(request)
        events: List[Dict[str, Any]] = [
            {
                "event": "accepted",
                "model_id": request.model_id,
                "runtime_mode": request.runtime_mode,
                "modalities": sorted(request.modalities.keys()),
            },
            {
                "event": "plan",
                "steps": [step.model_dump() for step in plan.steps],
            },
        ]
        for step in plan.steps:
            events.append(
                {
                    "event": "progress",
                    "step": step.order,
                    "name": step.name,
                    "detail": step.detail,
                }
            )
        events.append({"event": "result", "payload": response.model_dump()})
        return events

    def _try_research_inference(self, request: InferenceRequest) -> InferenceResponse | None:
        if torch is None:
            return None
        descriptor = RESEARCH_MODELS.get(request.model_id)
        if descriptor is None or not descriptor.supports_research_mode or descriptor.loader is None:
            return None

        arrays = arrays_from_request(request)
        torch_inputs = {
            modality: torch.tensor(array, dtype=torch.float32)
            for modality, array in arrays.items()
        }
        warnings: List[str] = []

        if request.model_id == "adaptive_transformer":
            factory = descriptor.loader()
            modality_specs = {
                modality: (
                    int(array.shape[-1]),
                    min(max(int(array.shape[-1]), 64), self.settings.default_hidden_dim),
                    self.settings.default_hidden_dim,
                )
                for modality, array in arrays.items()
            }
            model = factory(
                modality_specs=modality_specs,
                global_hidden_dim=self.settings.default_hidden_dim,
                num_classes=request.num_classes,
            )
            model.eval()
            with torch.no_grad():
                result = model(
                    torch_inputs,
                    return_embeddings=request.return_embeddings,
                    return_uncertainty=request.return_uncertainty,
                )
        elif request.model_id == "complete_multimodal":
            factory = descriptor.loader()
            model_size = "small" if self.settings.default_hidden_dim <= 384 else "base"
            model = factory(model_size=model_size, num_classes=request.num_classes or 4)
            model.eval()
            task = "classification" if request.target == "classification" else "retrieval"
            with torch.no_grad():
                result = model(torch_inputs, task=task, return_embeddings=request.return_embeddings)
        else:
            return None

        outputs: Dict[str, Any] = {}
        summaries: Dict[str, OutputSummary] = {}
        for key, value in result.items():
            if not hasattr(value, "detach"):
                outputs[key] = value
                continue
            array = value.detach().cpu().numpy()
            summaries[key] = output_summary(array)
            flat = array.reshape(array.shape[0], -1) if array.ndim > 1 else array.reshape(1, -1)
            outputs[key] = flat[:, : min(8, flat.shape[1])].tolist()

        if not outputs:
            warnings.append(
                "Research runtime returned no serializable outputs; inspect "
                "the raw model lane locally."
            )
        plan = self.plan(request)
        return InferenceResponse(
            model_id=request.model_id,
            runtime_mode="research",
            route=[step.name for step in plan.steps],
            outputs=outputs,
            summaries=summaries,
            warnings=warnings,
        )

    def _benchmark_request(self, model_id: str) -> InferenceRequest:
        text_values = np.linspace(-1.0, 1.0, 16, dtype=np.float32).tolist()
        image_values = np.linspace(0.0, 1.0, 24, dtype=np.float32).tolist()
        return InferenceRequest(
            model_id=model_id,
            runtime_mode="contract",
            target="embedding",
            modalities={
                "text": {"shape": [2, 8], "values": text_values},
                "image": {"shape": [2, 12], "values": image_values},
            },
        )
