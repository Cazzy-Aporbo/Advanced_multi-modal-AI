from __future__ import annotations

import math
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
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
    BenchmarkStageResult,
    BiasAssessmentRequest,
    BiasAssessmentResponse,
    BiasCategory,
    ChangeControlRecord,
    ChangeControlRequest,
    ComplianceLedgerToken,
    ConnectorPipelineIngestRequest,
    ConnectorPipelineIngestResponse,
    ConnectorRegistrationRequest,
    ConnectorRegistrationResponse,
    ConnectorRunRecord,
    CymaticSurfaceBundle,
    DataLifecyclePolicyRecord,
    DataLifecyclePolicyRequest,
    DataProfileResponse,
    DatasetEvolutionRequest,
    DatasetEvolutionResponse,
    DatasetRecord,
    DatasetRegistrationRequest,
    DriftBaselineRecord,
    DriftBaselineRequest,
    ExecutionJournalSummary,
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
    ReferenceBenchmarkRequest,
    ReferenceBenchmarkResult,
    RepositoryPulse,
    ResearchSurfaceBundle,
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
    TensorInterceptResponse,
    TimeSpan,
    VideoCleaningRequest,
    VideoCleaningResponse,
    VideoPacketRequest,
    VideoPacketResponse,
)
from .cymatic_surface import build_cymatic_surface_bundle
from .domain_ontology import ingest_domain_ontology
from .drift import assess_population_drift, create_drift_baseline_record
from .drift_store import DriftStore
from .execution_journal_store import ExecutionJournalStore
from .governance_ledger import build_compliance_ledger_token
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
from .replay import build_replay_frames, compare_replay, export_pipeline_run
from .repository_pulse import build_repository_pulse
from .research_surfaces import (
    build_model_research_cards,
    build_research_surface_bundle,
)
from .retrieval import create_vector_index
from .rust_bridge import signature_from_payload, video_cuts_from_payload
from .signal_math import arrays_from_request, output_summary, signature
from .stewardship_store import StewardshipStore
from .tensor_guard import build_tensor_intercept_response
from .video import build_video_cleaning_response, build_video_packet

try:
    import torch
except Exception:  # pragma: no cover - optional dependency path
    torch = None


class PopulationDriftBlockedError(RuntimeError):
    def __init__(self, response: PopulationDriftResponse) -> None:
        super().__init__("population drift gate blocked inference")
        self.response = response


class TensorInterceptBlockedError(RuntimeError):
    def __init__(self, response: TensorInterceptResponse) -> None:
        super().__init__("tensor intercept gate blocked inference")
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
        self.execution_journal_store = ExecutionJournalStore(
            self.settings.execution_journal_db_path
        )

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

    def list_model_research_cards(self):
        record_data_plane("research_models")
        return build_model_research_cards(registered_models=self.list_models())

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

    def _runtime_store_counts(self) -> Dict[str, int]:
        return {
            "async_jobs": self.job_store.count_jobs(),
            "dataset_catalog": self.catalog_store.count_datasets(),
            "connector_runs": self.connector_store.count_runs(),
            "drift_baselines": self.drift_store.count_baselines(),
            "pipeline_runs": self.pipeline_store.count_runs(),
            "ontology_snapshots": self.ontology_store.count_snapshots(),
            "recipe_registry": self.recipe_store.count_recipes(),
            "lifecycle_policies": self.stewardship_store.count_lifecycle_policies(),
            "change_controls": self.stewardship_store.count_change_controls(),
            "supply_chain_snapshots": self.stewardship_store.count_supply_chain_snapshots(),
            "execution_journal_runs": self.execution_journal_store.count_records(),
        }

    def runtime_attestation(self) -> RuntimeAttestationResponse:
        record_data_plane("runtime_attestation")
        return build_runtime_attestation(
            settings=self.settings,
            store_counts=self._runtime_store_counts(),
        )

    def compliance_ledger_token(
        self,
        *,
        route: str,
        method: str,
        status_code: int,
    ) -> ComplianceLedgerToken:
        attestation = build_runtime_attestation(
            settings=self.settings,
            store_counts=self._runtime_store_counts(),
        )
        return build_compliance_ledger_token(
            attestation=attestation,
            route=route,
            method=method,
            status_code=status_code,
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

    def research_surface_bundle(self, route_count: int) -> ResearchSurfaceBundle:
        record_data_plane("research_surfaces")
        attestation = self.runtime_attestation()
        proof_bundle = build_runtime_proof_bundle(
            attestation=attestation,
            route_count=route_count,
        )
        readiness = build_readiness_report(
            attestation=attestation,
            proof_bundle=proof_bundle,
            recipes=self.recipe_store.list_recipes(limit=1000),
        )
        return build_research_surface_bundle(
            service_name=self.settings.service_name,
            version=self.settings.service_version,
            attestation=attestation,
            proof_bundle=proof_bundle,
            readiness=readiness,
            registered_models=self.list_models(),
        )

    def repository_pulse(self, route_count: int) -> RepositoryPulse:
        record_data_plane("repository_pulse")
        attestation = self.runtime_attestation()
        proof_bundle = build_runtime_proof_bundle(
            attestation=attestation,
            route_count=route_count,
        )
        readiness = build_readiness_report(
            attestation=attestation,
            proof_bundle=proof_bundle,
            recipes=self.recipe_store.list_recipes(limit=1000),
        )
        return build_repository_pulse(
            settings=self.settings,
            attestation=attestation,
            execution_journal=self.execution_journal_store.build_summary(limit=20),
            proof_bundle=proof_bundle,
            readiness=readiness,
            model_cards=self.list_model_research_cards(),
        )

    def cymatic_surface_bundle(self, route_count: int) -> CymaticSurfaceBundle:
        record_data_plane("cymatic_surface")
        return build_cymatic_surface_bundle(
            research_bundle=self.research_surface_bundle(route_count=route_count),
            repository_pulse=self.repository_pulse(route_count=route_count),
            benchmark=self.run_reference_benchmark(
                route_count=route_count,
                request=ReferenceBenchmarkRequest(),
            ),
            execution_journal=self.execution_journal(limit=12),
        )

    def execution_journal(self, limit: int = 20) -> ExecutionJournalSummary:
        record_data_plane("execution_journal")
        return self.execution_journal_store.build_summary(limit=limit)

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
        profile = build_data_profile(request)
        intercept = self.inspect_tensor_request(request)
        return profile.model_copy(
            update={
                "tensor_intercepts": intercept.intercept_profiles,
                "warnings": [*intercept.warnings, *profile.warnings],
            }
        )

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
        profile = self.profile_request(request.request)
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
        profile = self.profile_request(request.request)
        return assess_population_drift(baseline=baseline, current_profile=profile, request=request)

    def ingest_pipeline_batch(self, request: PipelineIngestRequest) -> PipelineRunRecord:
        record_data_plane("pipeline_ingest")
        inference_request, modality_counts, dropped_events = (
            build_inference_request_from_pipeline(request)
        )
        replay_frames = build_replay_frames(
            events=request.events,
            stream_id=request.stream_id,
            batch_label=request.batch_label,
            settings=self.settings,
        )
        profile = self.profile_request(inference_request)
        provenance = build_provenance_receipt(inference_request)
        notes = list(request.notes)
        if dropped_events:
            notes.append(
                f"{dropped_events} events were held out because the modalities "
                "were paired to the narrowest shared batch."
            )
        if replay_frames:
            notes.append(
                f"{len(replay_frames)} replay frames were sealed into the execution memory."
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
            replay_frames=replay_frames,
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
        replay_frames = build_replay_frames(
            events=record.event_lineage,
            stream_id=record.stream_id,
            batch_label=record.batch_label,
            settings=self.settings,
        )
        return compare_replay(
            record=record,
            replay_response=replay_response,
            replay_provenance_digest=replay_provenance.payload_digest,
            replay_frames=replay_frames,
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
            max_workers_used = min(max(request.max_workers, 1), len(request.requests))
            job_started = perf_counter()
            item_results: list[dict[str, Any]] = []
            result_payloads: list[dict[str, Any]] = []

            def _run_one(index: int, item: InferenceRequest) -> dict[str, Any]:
                started = perf_counter()
                try:
                    response = self.infer(item)
                except Exception as error:  # pragma: no cover - exercised through job lane tests
                    error_payload = getattr(error, "response", None)
                    failure_detail = (
                        error_payload.model_dump(mode="json")
                        if error_payload is not None
                        else {"message": str(error)}
                    )
                    return {
                        "index": index,
                        "status": "failed",
                        "duration_ms": float((perf_counter() - started) * 1000),
                        "model_id": item.model_id,
                        "runtime_mode": item.runtime_mode,
                        "target": item.target,
                        "modalities": sorted(item.modalities.keys()),
                        "error": failure_detail,
                    }

                payload = response.model_dump(mode="json")
                return {
                    "index": index,
                    "status": "completed",
                    "duration_ms": float((perf_counter() - started) * 1000),
                    "model_id": item.model_id,
                    "runtime_mode": item.runtime_mode,
                    "target": item.target,
                    "modalities": sorted(item.modalities.keys()),
                    "route": payload.get("route", []),
                    "warning_count": len(payload.get("warnings", [])),
                    "response": payload,
                }

            with ThreadPoolExecutor(max_workers=max_workers_used) as executor:
                future_to_index = {
                    executor.submit(_run_one, index, item): index
                    for index, item in enumerate(request.requests)
                }
                for future in as_completed(future_to_index):
                    item_result = future.result()
                    item_results.append(item_result)
                    if item_result["status"] == "completed":
                        result_payloads.append(item_result["response"])

            ordered_items = sorted(item_results, key=lambda item: int(item["index"]))
            latencies = sorted(float(item["duration_ms"]) for item in ordered_items)
            completed_count = sum(1 for item in ordered_items if item["status"] == "completed")
            failed_count = len(ordered_items) - completed_count
            self.job_store.mark_completed(
                job_id,
                {
                    "label": request.label,
                    "record_count": len(ordered_items),
                    "succeeded_count": completed_count,
                    "failed_count": failed_count,
                    "max_workers_requested": request.max_workers,
                    "max_workers_used": max_workers_used,
                    "median_latency_ms": float(median(latencies)) if latencies else 0.0,
                    "p95_latency_ms": float(self._p95(latencies)),
                    "total_duration_ms": float((perf_counter() - job_started) * 1000),
                    "results": result_payloads,
                    "items": ordered_items,
                },
            )
        except Exception as error:  # pragma: no cover - defensive async lane
            self.job_store.mark_failed(job_id, str(error))

    def get_job(self, job_id: str) -> AsyncJobRecord | None:
        return self.job_store.get_job(job_id)

    def list_jobs(self, limit: int = 20) -> List[AsyncJobRecord]:
        return self.job_store.list_jobs(limit=limit)

    def inspect_tensor_request(self, request: InferenceRequest) -> TensorInterceptResponse:
        record_data_plane("tensor_intercept")
        return build_tensor_intercept_response(request=request, settings=self.settings)

    def infer(self, request: InferenceRequest) -> InferenceResponse:
        intercept_result = self.inspect_tensor_request(request)
        if intercept_result.blocked:
            raise TensorInterceptBlockedError(intercept_result)
        intercept_warnings = list(intercept_result.warnings)
        drift_result = self._maybe_run_population_drift_gate(request)
        drift_warnings = self._drift_warnings(drift_result) if drift_result is not None else []
        with observe_inference(request.runtime_mode, request.model_id):
            if request.runtime_mode == "research":
                research_result = self._try_research_inference(request)
                if research_result is not None:
                    if intercept_warnings or drift_warnings:
                        research_result.warnings = (
                            intercept_warnings + drift_warnings + research_result.warnings
                        )
                    return research_result
            response = self._contract_inference(
                request,
                fallback_from_research=request.runtime_mode == "research",
            )
            if intercept_warnings or drift_warnings:
                response.warnings = intercept_warnings + drift_warnings + response.warnings
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

    def run_reference_benchmark(
        self,
        *,
        route_count: int,
        request: ReferenceBenchmarkRequest | None = None,
    ) -> ReferenceBenchmarkResult:
        benchmark_request = request or ReferenceBenchmarkRequest()
        benchmark_id = str(uuid4())
        total_started = perf_counter()
        row_count = max(benchmark_request.batch_size, 3)
        stages: list[BenchmarkStageResult] = []
        pipeline_run_id = ""
        replay_frame_count = 0
        replay_verified = False
        notes = [
            (
                "This benchmark uses deterministic reference fixtures to "
                "exercise live repository lanes."
            ),
            (
                "It is meant to prove orchestration paths, persistence, "
                "and evidence export together."
            ),
        ]

        def record_stage(
            *,
            stage_id: str,
            label: str,
            started: float,
            status: str,
            record_count: int = 0,
            stage_notes: list[str] | None = None,
            artifacts: list[str] | None = None,
        ) -> None:
            stages.append(
                BenchmarkStageResult(
                    stage_id=stage_id,
                    label=label,
                    duration_ms=float((perf_counter() - started) * 1000),
                    status=status,
                    record_count=record_count,
                    notes=stage_notes or [],
                    artifacts=artifacts or [],
                )
            )

        inference_request = self._benchmark_request(
            model_id=benchmark_request.model_id,
            batch_size=row_count,
        )

        if benchmark_request.include_connector_ingest:
            connector_started = perf_counter()
            import pyarrow as pa
            import pyarrow.parquet as pq

            dataset_name = f"reference_signal_rows_{benchmark_id[:8]}"
            with tempfile.TemporaryDirectory(prefix="amai-reference-benchmark-") as temp_dir:
                parquet_path = Path(temp_dir) / "reference_signal.parquet"
                reference_rows = self._reference_connector_rows(row_count)
                table = pa.table(
                    {
                        key: [row[key] for row in reference_rows]
                        for key in reference_rows[0]
                    }
                )
                pq.write_table(table, parquet_path)

                connector_result = self.connector_pipeline_ingest(
                    ConnectorPipelineIngestRequest(
                        connector={"kind": "local_parquet", "source": str(parquet_path)},
                        dataset_name=dataset_name,
                        owner="reference-benchmark",
                        version=datetime.now(timezone.utc).strftime("%Y.%m.%d"),
                        stream_id=f"reference-stream-{benchmark_id[:8]}",
                        batch_label=benchmark_request.label,
                        modality_mappings=[
                            {
                                "modality": "tabular",
                                "feature_fields": ["tab_a", "tab_b", "tab_c"],
                                "source": "reference-tabular-lane",
                            },
                            {
                                "modality": "sensor",
                                "feature_fields": ["sensor_a", "sensor_b", "sensor_c"],
                                "source": "reference-sensor-lane",
                            },
                        ],
                        partition_key_field="capture_day",
                        tags=["reference-benchmark", "connector-proof"],
                        notes=[
                            "Parquet-backed reference workload for the public benchmark surface."
                        ],
                    )
                )

            connector_benchmark = connector_result.connector_run.benchmark
            record_stage(
                stage_id="connector_ingest",
                label="Connector-backed Parquet ingest",
                started=connector_started,
                status="pass",
                record_count=connector_result.connector_run.record_count,
                stage_notes=[
                    (
                        f"{connector_benchmark.parser} pulled "
                        f"{connector_benchmark.record_count} rows at "
                        f"{connector_benchmark.rows_per_second:.1f} rows/s."
                    ),
                    (
                        "Zero-copy candidate: "
                        f"{'yes' if connector_benchmark.zero_copy_path else 'no'}."
                    ),
                ],
                artifacts=[
                    connector_result.connector_run.run_id,
                    connector_result.pipeline_run.run_id,
                ],
            )

            pipeline_run_id = connector_result.pipeline_run.run_id
            replay_frame_count = len(connector_result.pipeline_run.replay_frames)

            replay_started = perf_counter()
            pipeline_export = self.export_pipeline_run(connector_result.pipeline_run.run_id)
            pipeline_replay = self.replay_pipeline_run(connector_result.pipeline_run.run_id)
            replay_verified = bool(
                pipeline_replay is not None
                and pipeline_replay.provenance_match
                and pipeline_replay.frame_parity_match
            )
            export_digest = ""
            if pipeline_export is not None:
                export_digest = next(
                    (
                        item.sha256[:16]
                        for item in pipeline_export.artifact_digests
                        if item.artifact == "replay_frames"
                    ),
                    "",
                )
            replay_notes = [
                f"Replay frames sealed: {replay_frame_count}.",
                f"Frame parity: {'verified' if replay_verified else 'watch'}.",
            ]
            if export_digest:
                replay_notes.append(f"Replay digest head: {export_digest}…")
            if pipeline_replay is not None:
                replay_notes.append(
                    f"Recorded head: {pipeline_replay.recorded_head_digest[:16]}…"
                )
                replay_notes.append(
                    f"Replayed head: {pipeline_replay.replayed_head_digest[:16]}…"
                )
            record_stage(
                stage_id="pipeline_replay",
                label="Pipeline replay ledger",
                started=replay_started,
                status="pass" if replay_verified else "watch",
                record_count=replay_frame_count,
                stage_notes=replay_notes,
                artifacts=[connector_result.pipeline_run.run_id, "replay_frames"],
            )

        profile_started = perf_counter()
        profile_result = self.profile_request(inference_request)
        record_stage(
            stage_id="profile_lane",
            label="Cross-modal profile lane",
            started=profile_started,
            status="pass" if profile_result.fusion_readiness >= 0.5 else "watch",
            record_count=len(profile_result.modality_profiles),
            stage_notes=[
                f"Fusion readiness: {profile_result.fusion_readiness:.3f}.",
                f"Coverage score: {profile_result.coverage_score:.3f}.",
                (
                    "Tensor intercept watch points: "
                    f"{sum(1 for item in profile_result.tensor_intercepts if item.status != 'ok')}."
                ),
            ],
            artifacts=["/v1/data/profile"],
        )

        provenance_started = perf_counter()
        provenance_result = self.build_provenance(inference_request)
        record_stage(
            stage_id="provenance_lane",
            label="Payload provenance receipt",
            started=provenance_started,
            status="pass",
            record_count=len(provenance_result.modality_digests),
            stage_notes=[
                f"Payload digest: {provenance_result.payload_digest[:16]}…",
                f"Metadata digest: {provenance_result.metadata_digest[:16]}…",
            ],
            artifacts=[provenance_result.receipt_id],
        )

        if benchmark_request.include_batch_job:
            batch_started = perf_counter()
            batch_job_request = BatchInferenceRequest(
                label=f"{benchmark_request.label}-batch",
                max_workers=benchmark_request.max_workers,
                requests=self._reference_batch_requests(
                    model_id=benchmark_request.model_id,
                    batch_size=row_count,
                ),
            )
            submission = self.submit_batch_inference_job(batch_job_request)
            self.run_batch_inference_job(submission.job_id, batch_job_request)
            batch_record = self.get_job(submission.job_id)
            batch_payload = batch_record.result_payload if batch_record is not None else {}
            record_stage(
                stage_id="batch_job",
                label="Persisted concurrent batch lane",
                started=batch_started,
                status="pass" if batch_payload.get("failed_count", 0) == 0 else "watch",
                record_count=int(batch_payload.get("record_count", 0)),
                stage_notes=[
                    (
                        f"Workers used: {batch_payload.get('max_workers_used', 0)} "
                        f"of {batch_payload.get('max_workers_requested', 0)} requested."
                    ),
                    (
                        f"Median latency: {batch_payload.get('median_latency_ms', 0.0):.2f} ms."
                    ),
                    (
                        f"Failed items: {batch_payload.get('failed_count', 0)}."
                    ),
                ],
                artifacts=[submission.job_id],
            )

        recipe_started = perf_counter()
        recipe_record = self.compile_recipe(
            RecipeCompileRequest(
                label=f"{benchmark_request.label}-recipe",
                owner="reference-benchmark",
                objective="alignment_eval",
                model={
                    "model_ref": benchmark_request.model_id,
                    "family": "multimodal",
                    "adapter_kind": "none",
                    "precision": "fp16",
                    "target_modules": ["fusion_gate"],
                },
                sources=[
                    {
                        "split": "train",
                        "modality": "tabular",
                        "dataset_name": f"reference_signal_rows_{benchmark_id[:8]}",
                        "expected_rows": row_count,
                        "notes": ["Reference benchmark dataset contract."],
                    }
                ]
                if benchmark_request.include_connector_ingest
                else [
                    {
                        "split": "train",
                        "modality": "text",
                        "source_uri": "inline://reference-benchmark",
                        "expected_rows": row_count,
                        "notes": ["Reference benchmark inline lane."],
                    }
                ],
                training={
                    "epochs": 1.0,
                    "micro_batch_size": 1,
                    "gradient_accumulation_steps": 2,
                },
                distributed={
                    "engine": "local",
                    "node_count": 1,
                    "devices_per_node": 1,
                    "zero_stage": 0,
                },
                evaluation={
                    "metrics": ["loss", "calibration"],
                    "primary_metric": "calibration",
                },
                tags=["reference-benchmark", "recipe-proof"],
            )
        )
        resolved_source_count = sum(
            1 for item in recipe_record.resolved_sources if item.resolved
        )
        estimated_global_batch = (
            recipe_record.launch_profile.estimated_global_batch_size
            if recipe_record.launch_profile
            else 0
        )
        record_stage(
            stage_id="recipe_compile",
            label="Recipe registry handoff",
            started=recipe_started,
            status="pass",
            record_count=max(len(recipe_record.sources), 1),
            stage_notes=[
                f"Distributed engine: {recipe_record.distributed.engine}.",
                f"Resolved sources: {resolved_source_count}.",
                f"Estimated global batch: {estimated_global_batch}.",
            ],
            artifacts=[recipe_record.recipe_id],
        )

        if benchmark_request.include_smoke_benchmark:
            smoke_started = perf_counter()
            smoke_result = self.run_smoke_benchmark(
                model_id=benchmark_request.model_id,
                iterations=max(6, row_count),
            )
            record_stage(
                stage_id="smoke_benchmark",
                label="Deterministic latency check",
                started=smoke_started,
                status="pass",
                record_count=smoke_result.iterations,
                stage_notes=[
                    f"Median latency: {smoke_result.median_latency_ms:.2f} ms.",
                    f"P95 latency: {smoke_result.p95_latency_ms:.2f} ms.",
                ],
                artifacts=[smoke_result.benchmark_id],
            )

        proof_started = perf_counter()
        proof_bundle = self.runtime_proof_bundle(route_count=route_count)
        record_stage(
            stage_id="proof_bundle",
            label="Runtime proof surface snapshot",
            started=proof_started,
            status="pass",
            record_count=proof_bundle.verification_artifact_count,
            stage_notes=[
                f"Route count: {proof_bundle.route_count}.",
                f"Verification artifacts: {proof_bundle.verification_artifact_count}.",
                f"Connector kinds: {', '.join(proof_bundle.connector_kinds)}.",
            ],
            artifacts=["proof/runtime-proof.json"],
        )

        return ReferenceBenchmarkResult(
            benchmark_id=benchmark_id,
            label=benchmark_request.label,
            model_id=benchmark_request.model_id,
            route_count=route_count,
            verification_artifact_count=proof_bundle.verification_artifact_count,
            stage_count=len(stages),
            row_count=row_count,
            pipeline_run_id=pipeline_run_id,
            replay_frame_count=replay_frame_count,
            replay_verified=replay_verified,
            total_duration_ms=float((perf_counter() - total_started) * 1000),
            stages=stages,
            notes=notes,
        )

    def _p95(self, ordered_latencies: list[float]) -> float:
        if not ordered_latencies:
            return 0.0
        p95_index = max(int(len(ordered_latencies) * 0.95) - 1, 0)
        return float(ordered_latencies[p95_index])

    def _reference_connector_rows(self, row_count: int) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for index in range(row_count):
            rows.append(
                {
                    "event_id": f"evt-{index + 1:03d}",
                    "capture_day": f"2026-07-{(index % 9) + 1:02d}",
                    "tab_a": round(0.42 + (index * 0.06), 4),
                    "tab_b": round(0.58 + (index * 0.05), 4),
                    "tab_c": round(0.64 + (index * 0.04), 4),
                    "sensor_a": round(0.18 + (index * 0.07), 4),
                    "sensor_b": round(0.24 + (index * 0.06), 4),
                    "sensor_c": round(0.31 + (index * 0.05), 4),
                }
            )
        return rows

    def _reference_batch_requests(
        self, *, model_id: str, batch_size: int
    ) -> list[InferenceRequest]:
        requests: list[InferenceRequest] = []
        for index in range(batch_size):
            base = 0.1 + (index * 0.08)
            requests.append(
                InferenceRequest(
                    model_id=model_id,
                    runtime_mode="contract",
                    target="classification" if index % 2 else "embedding",
                    num_classes=3 if index % 2 else None,
                    metadata={
                        "request_id": f"reference-batch-{index + 1:02d}",
                        "population_baseline_label": "",
                    },
                    modalities={
                        "text": {
                            "shape": [1, 4],
                            "values": [
                                round(base, 4),
                                round(base + 0.12, 4),
                                round(base + 0.24, 4),
                                round(base + 0.36, 4),
                            ],
                        },
                        "audio": {
                            "shape": [1, 4],
                            "values": [
                                round(base + 0.04, 4),
                                round(base + 0.16, 4),
                                round(base + 0.2, 4),
                                round(base + 0.32, 4),
                            ],
                        },
                    },
                )
            )
        return requests

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

    def _benchmark_request(self, model_id: str, batch_size: int = 2) -> InferenceRequest:
        feature_width = 8
        text_values = [
            round((((row * 0.17) + (column * 0.11)) % 1.6) - 0.8, 6)
            for row in range(batch_size)
            for column in range(feature_width)
        ]
        image_values = [
            round(((row * 0.09) + (column * 0.05)) % 1.0, 6)
            for row in range(batch_size)
            for column in range(12)
        ]
        return InferenceRequest(
            model_id=model_id,
            runtime_mode="contract",
            target="embedding",
            modalities={
                "text": {"shape": [batch_size, feature_width], "values": text_values},
                "image": {"shape": [batch_size, 12], "values": image_values},
            },
        )
