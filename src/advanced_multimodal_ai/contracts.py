from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

ModalityKind = Literal["text", "image", "audio", "video", "sensor", "tabular"]
RuntimeMode = Literal["contract", "research"]
TargetKind = Literal["embedding", "classification", "retrieval", "translation"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TensorPayload(BaseModel):
    shape: List[int] = Field(min_length=2, description="Tensor shape, e.g. [batch, seq, dim]")
    values: List[float] = Field(description="Flattened tensor values in row-major order")
    dtype: str = "float32"

    @field_validator("shape")
    @classmethod
    def validate_shape(cls, value: List[int]) -> List[int]:
        if any(dimension <= 0 for dimension in value):
            raise ValueError("All tensor dimensions must be positive")
        return value

    @model_validator(mode="after")
    def validate_values_length(self) -> "TensorPayload":
        total = 1
        for dimension in self.shape:
            total *= dimension
        if total != len(self.values):
            raise ValueError(
                "Tensor payload expected "
                f"{total} values from shape {self.shape}, "
                f"received {len(self.values)}"
            )
        return self


class InferenceRequest(BaseModel):
    model_id: str = "adaptive_transformer"
    runtime_mode: RuntimeMode = "contract"
    target: TargetKind = "embedding"
    num_classes: Optional[int] = Field(default=None, ge=2)
    return_embeddings: bool = True
    return_uncertainty: bool = False
    modalities: Dict[ModalityKind, TensorPayload]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_modalities(self) -> "InferenceRequest":
        if not self.modalities:
            raise ValueError("At least one modality payload is required")
        return self


class PlanStep(BaseModel):
    order: int
    name: str
    detail: str


class OrchestrationPlan(BaseModel):
    request_id: str
    model_id: str
    runtime_mode: RuntimeMode
    target: TargetKind
    source_modalities: List[ModalityKind]
    steps: List[PlanStep]
    created_at: str = Field(default_factory=utc_now)


class OutputSummary(BaseModel):
    shape: List[int]
    mean: float
    std: float
    min: float
    max: float


class InferenceResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    model_id: str
    runtime_mode: RuntimeMode
    route: List[str]
    outputs: Dict[str, Any]
    summaries: Dict[str, OutputSummary]
    warnings: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class HealthResponse(BaseModel):
    service: str
    version: str
    environment: str
    status: Literal["ok", "degraded"]
    torch_available: bool
    metrics_enabled: bool
    created_at: str = Field(default_factory=utc_now)


class RegisteredModelResponse(BaseModel):
    model_id: str
    label: str
    runtime_ready: bool
    supports_contract_mode: bool
    supports_research_mode: bool
    source_file: str
    notes: str


class ModelResearchQuestion(BaseModel):
    prompt: str
    why_it_matters: str
    current_position: str


class ModelResearchCard(BaseModel):
    model_id: str
    label: str
    source_file: str
    runtime_ready: bool
    supports_contract_mode: bool
    supports_research_mode: bool
    role_in_system: str
    why_used: str
    strengths: List[str] = Field(default_factory=list)
    limits: List[str] = Field(default_factory=list)
    improvement_paths: List[str] = Field(default_factory=list)
    evidence_surfaces: List[str] = Field(default_factory=list)
    related_files: List[str] = Field(default_factory=list)
    open_questions: List[ModelResearchQuestion] = Field(default_factory=list)


class RepositoryFinding(BaseModel):
    finding_id: str
    lens: Literal["runtime", "research", "data", "governance", "evaluation"]
    title: str
    summary: str
    evidence: List[str] = Field(default_factory=list)
    why_it_matters: str
    next_step: str
    related_surfaces: List[str] = Field(default_factory=list)
    related_files: List[str] = Field(default_factory=list)


class RepositoryConnection(BaseModel):
    connection_id: str
    title: str
    summary: str
    files: List[str] = Field(default_factory=list)
    api_surfaces: List[str] = Field(default_factory=list)
    learning_value: str
    watch_points: List[str] = Field(default_factory=list)


class ArchitectureLane(BaseModel):
    lane_id: str
    label: str
    layer: Literal["frontend", "backend", "compiled", "client", "evidence"]
    purpose: str
    directories: List[str] = Field(default_factory=list)
    entry_surfaces: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    proof_points: List[str] = Field(default_factory=list)
    why_it_exists: str


class ResearchSurfaceSummary(BaseModel):
    route_count: int = Field(ge=0)
    test_count: int = Field(ge=0)
    connector_kind_count: int = Field(ge=0)
    model_count: int = Field(ge=0)
    runtime_ready_model_count: int = Field(ge=0)
    open_question_count: int = Field(ge=0)
    generated_at: str = Field(default_factory=utc_now)


class PulseArtifact(BaseModel):
    label: str
    path: str
    exists: bool
    bytes: int = Field(default=0, ge=0)
    modified_at: Optional[str] = None
    status: Literal["pass", "watch", "missing"]
    note: str


class PulseLane(BaseModel):
    lane_id: str
    label: str
    emphasis: Literal["frontend", "backend", "compiled", "client", "evidence", "models"]
    live_score: int = Field(ge=0, le=100)
    summary: str
    active_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    files: List[str] = Field(default_factory=list)
    artifacts: List[PulseArtifact] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)


class RepositoryPulse(BaseModel):
    service: str
    version: str
    route_count: int = Field(ge=0)
    test_count: int = Field(ge=0)
    model_count: int = Field(ge=0)
    readiness_posture: ReadinessPosture
    lanes: List[PulseLane] = Field(default_factory=list)
    generated_at: str = Field(default_factory=utc_now)


class RetrievalRecord(BaseModel):
    record_id: str
    modality: ModalityKind
    vector: List[float] = Field(min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("vector")
    @classmethod
    def validate_vector(cls, value: List[float]) -> List[float]:
        if any(not isinstance(item, (int, float)) for item in value):
            raise ValueError("Retrieval vectors must contain numeric values only")
        if any(item != item or item in {float("inf"), float("-inf")} for item in value):
            raise ValueError("Retrieval vectors must contain finite numeric values only")
        return value


class RetrievalUpsertRequest(BaseModel):
    records: List[RetrievalRecord] = Field(min_length=1)


class RetrievalQueryRequest(BaseModel):
    modality: ModalityKind
    vector: List[float] = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=25)
    metadata_filter: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("vector")
    @classmethod
    def validate_query_vector(cls, value: List[float]) -> List[float]:
        if any(item != item or item in {float("inf"), float("-inf")} for item in value):
            raise ValueError("Query vectors must contain finite numeric values only")
        return value


class RetrievalMatch(BaseModel):
    record_id: str
    modality: ModalityKind
    score: float
    metadata: Dict[str, Any]


class RetrievalQueryResponse(BaseModel):
    matches: List[RetrievalMatch]
    backend: str
    created_at: str = Field(default_factory=utc_now)


class TranscriptToken(BaseModel):
    token: str = Field(min_length=1)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    speaker: Optional[str] = None

    @model_validator(mode="after")
    def validate_span(self) -> "TranscriptToken":
        if self.end_ms <= self.start_ms:
            raise ValueError("Transcript tokens must end after they start")
        return self


class FrameSignal(BaseModel):
    index: int = Field(ge=0)
    timestamp_ms: int = Field(ge=0)
    motion_score: float = 0.0
    focus_score: float = 0.0
    brightness: float = 0.0


class AudioEnergyPoint(BaseModel):
    timestamp_ms: int = Field(ge=0)
    energy: float = Field(ge=0.0)


class TimeSpan(BaseModel):
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_span(self) -> "TimeSpan":
        if self.end_ms <= self.start_ms:
            raise ValueError("Time spans must end after they start")
        return self


class VideoPacketRequest(BaseModel):
    clip_id: str
    duration_ms: int = Field(gt=0)
    transcript: List[TranscriptToken] = Field(default_factory=list)
    frames: List[FrameSignal] = Field(default_factory=list)
    audio_energy: List[AudioEnergyPoint] = Field(default_factory=list)
    objective: Literal["cleanup", "summary", "retrieval", "qa"] = "cleanup"

    @model_validator(mode="after")
    def validate_ordering(self) -> "VideoPacketRequest":
        last_end = -1
        for token in self.transcript:
            if token.start_ms < last_end:
                raise ValueError("Transcript tokens must arrive in chronological order")
            last_end = token.end_ms
        return self


class SuggestedCut(BaseModel):
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    reason: str
    severity: Literal["low", "medium", "high"] = "medium"
    transcript_excerpt: str = ""

    @model_validator(mode="after")
    def validate_span(self) -> "SuggestedCut":
        if self.end_ms <= self.start_ms:
            raise ValueError("Suggested cuts must end after they start")
        return self


class VideoEvidenceWindow(BaseModel):
    span: TimeSpan
    transcript_excerpt: str
    average_motion: float
    average_focus: float
    average_audio_energy: float
    note: str


class VideoPacketResponse(BaseModel):
    clip_id: str
    objective: str
    evidence_windows: List[VideoEvidenceWindow]
    cut_candidates: List[SuggestedCut]
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class VideoCleaningRequest(VideoPacketRequest):
    silence_threshold_ms: int = Field(default=650, ge=150, le=3000)
    filler_words: List[str] = Field(
        default_factory=lambda: ["um", "uh", "erm", "ah", "like", "you know"]
    )
    max_cut_ms: int = Field(default=2200, ge=100, le=10000)


class VideoCleaningResponse(BaseModel):
    clip_id: str
    removed_spans: List[SuggestedCut]
    retained_spans: List[TimeSpan]
    kept_duration_ms: int
    removed_duration_ms: int
    cut_script: List[str]
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class BenchmarkResult(BaseModel):
    benchmark_id: str
    runtime_mode: RuntimeMode
    model_id: str
    iterations: int
    median_latency_ms: float
    p95_latency_ms: float
    notes: str
    created_at: str = Field(default_factory=utc_now)


JobStatus = Literal["queued", "running", "completed", "failed"]


class BatchInferenceRequest(BaseModel):
    label: str = "batch-inference"
    requests: List[InferenceRequest] = Field(min_length=1, max_length=64)


class AsyncJobSubmissionResponse(BaseModel):
    job_id: str
    kind: Literal["video_clean", "batch_infer"]
    status: JobStatus
    submitted_at: str = Field(default_factory=utc_now)
    record_count: int = Field(ge=1)


class AsyncJobRecord(BaseModel):
    job_id: str
    kind: Literal["video_clean", "batch_infer"]
    status: JobStatus
    submitted_at: str
    started_at: str = ""
    completed_at: str = ""
    record_count: int = Field(ge=1)
    request_payload: Dict[str, Any]
    result_payload: Dict[str, Any] = Field(default_factory=dict)
    error_message: str = ""


class ModalityQualityProfile(BaseModel):
    modality: ModalityKind
    batch_size: int = Field(ge=1)
    feature_width: int = Field(ge=1)
    value_count: int = Field(ge=1)
    finite_ratio: float = Field(ge=0.0, le=1.0)
    zero_ratio: float = Field(ge=0.0, le=1.0)
    entropy_score: float = Field(ge=0.0, le=1.0)
    energy_score: float = Field(ge=0.0)
    dynamic_range: float = Field(ge=0.0)
    temporal_change: float = Field(ge=0.0)
    status: Literal["ok", "watch", "fail"]
    notes: List[str] = Field(default_factory=list)


class PairwiseAlignmentProfile(BaseModel):
    left_modality: ModalityKind
    right_modality: ModalityKind
    cosine_alignment: float = Field(ge=-1.0, le=1.0)
    mean_gap: float = Field(ge=0.0)
    note: str


class DataProfileResponse(BaseModel):
    request_id: str
    model_id: str
    runtime_mode: RuntimeMode
    modality_profiles: List[ModalityQualityProfile]
    pairwise_alignment: List[PairwiseAlignmentProfile]
    coverage_score: float = Field(ge=0.0, le=1.0)
    fusion_readiness: float = Field(ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class ProvenanceReceipt(BaseModel):
    receipt_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    model_id: str
    runtime_mode: RuntimeMode
    modality_digests: Dict[ModalityKind, str]
    metadata_digest: str
    payload_digest: str
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class TemporalObservation(BaseModel):
    modality: ModalityKind
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_id: str = ""
    note: str = ""
    attributes: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_window(self) -> "TemporalObservation":
        if self.end_ms <= self.start_ms:
            raise ValueError("Temporal observations must end after they start")
        return self


class TemporalAlignmentRequest(BaseModel):
    observations: List[TemporalObservation] = Field(min_length=1)
    merge_gap_ms: int = Field(default=120, ge=0, le=3000)
    minimum_modalities: int = Field(default=2, ge=1, le=6)
    include_singletons: bool = False


class TemporalAlignmentWindow(BaseModel):
    span: TimeSpan
    modalities: List[ModalityKind]
    observation_count: int = Field(ge=1)
    average_confidence: float = Field(ge=0.0, le=1.0)
    source_ids: List[str] = Field(default_factory=list)
    note: str


class TemporalAlignmentResponse(BaseModel):
    windows: List[TemporalAlignmentWindow]
    modality_coverage_ms: Dict[ModalityKind, int]
    uncovered_modalities: List[ModalityKind] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class DriftBaselineRequest(BaseModel):
    label: str = Field(min_length=1)
    request: InferenceRequest
    notes: List[str] = Field(default_factory=list)


class DriftBaselineRecord(BaseModel):
    baseline_id: str = Field(default_factory=lambda: str(uuid4()))
    label: str
    request_id: str
    model_id: str
    runtime_mode: RuntimeMode
    coverage_score: float = Field(ge=0.0, le=1.0)
    fusion_readiness: float = Field(ge=0.0, le=1.0)
    modality_profiles: List[ModalityQualityProfile]
    pairwise_alignment: List[PairwiseAlignmentProfile]
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class PopulationDriftRequest(BaseModel):
    baseline_label: str = Field(min_length=1)
    request: InferenceRequest
    max_entropy_shift: float = Field(default=0.25, ge=0.0, le=1.0)
    max_zero_shift: float = Field(default=0.25, ge=0.0, le=1.0)
    min_finite_ratio: float = Field(default=0.98, ge=0.0, le=1.0)
    max_alignment_drop: float = Field(default=0.35, ge=0.0, le=1.0)
    block_on_failure: bool = True


class ModalityDriftDelta(BaseModel):
    modality: ModalityKind
    entropy_shift: float = Field(ge=0.0)
    zero_shift: float = Field(ge=0.0)
    finite_shift: float
    dynamic_range_shift: float = Field(ge=0.0)
    temporal_change_shift: float = Field(ge=0.0)
    status: Literal["ok", "watch", "fail"]
    notes: List[str] = Field(default_factory=list)


class PopulationDriftResponse(BaseModel):
    baseline_label: str
    request_id: str
    model_id: str
    drift_score: float = Field(ge=0.0, le=1.0)
    blocked: bool
    modality_deltas: List[ModalityDriftDelta]
    alignment_drop: float = Field(ge=0.0)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


PipelineRunStatus = Literal["accepted", "blocked"]


class PipelineEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    source: str = Field(min_length=1)
    modality: ModalityKind
    observed_at: str = Field(default_factory=utc_now)
    tensor: TensorPayload
    partition_key: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineIngestRequest(BaseModel):
    stream_id: str = Field(min_length=1)
    batch_label: str = "default"
    model_id: str = "adaptive_transformer"
    runtime_mode: RuntimeMode = "contract"
    target: TargetKind = "embedding"
    num_classes: Optional[int] = Field(default=None, ge=2)
    baseline_label: str = ""
    block_population_drift: bool = True
    notes: List[str] = Field(default_factory=list)
    events: List[PipelineEvent] = Field(min_length=1, max_length=512)


class PipelineRunRecord(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    stream_id: str
    batch_label: str
    status: PipelineRunStatus
    model_id: str
    runtime_mode: RuntimeMode
    target: TargetKind
    event_count: int = Field(ge=1)
    paired_batch_size: int = Field(ge=1)
    dropped_events: int = Field(ge=0)
    modality_counts: Dict[ModalityKind, int]
    baseline_label: str = ""
    request_snapshot: Optional[InferenceRequest] = None
    event_lineage: List[PipelineEvent] = Field(default_factory=list)
    profile: DataProfileResponse
    provenance: ProvenanceReceipt
    drift: Optional[PopulationDriftResponse] = None
    inference: Optional[InferenceResponse] = None
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class ReplayArtifactDigest(BaseModel):
    artifact: str
    sha256: str


class PipelineRunExport(BaseModel):
    run_id: str
    stream_id: str
    batch_label: str
    status: PipelineRunStatus
    request_snapshot: Optional[InferenceRequest] = None
    event_lineage: List[PipelineEvent] = Field(default_factory=list)
    artifact_digests: List[ReplayArtifactDigest] = Field(default_factory=list)
    event_ndjson: str
    created_at: str = Field(default_factory=utc_now)


class PipelineReplayResponse(BaseModel):
    run_id: str
    replayed_at: str = Field(default_factory=utc_now)
    provenance_match: bool
    route_match: bool
    summary_shape_match: bool
    max_summary_mean_delta: float = Field(ge=0.0)
    replay_response: Optional[InferenceResponse] = None
    warnings: List[str] = Field(default_factory=list)


ControlDepth = Literal["surface", "context", "governance"]


class DomainArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(min_length=1)
    artifact_type: Literal[
        "api_schema",
        "workflow",
        "contract",
        "policy",
        "repo_manifest",
        "data_dictionary",
    ]
    control_depth: ControlDepth
    body: str = Field(min_length=1)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OntologyIngestRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    artifacts: List[DomainArtifact] = Field(min_length=1, max_length=256)
    zone_cells: Dict[str, List[str]] = Field(default_factory=dict)


class OntologyEntity(BaseModel):
    entity_id: str
    label: str
    kind: Literal["domain", "object", "action", "obligation", "dataset", "api", "jurisdiction"]
    control_depth: ControlDepth


class OntologyRelation(BaseModel):
    source_id: str
    relation: str
    target_id: str
    rationale: str


class GeometricConstraint(BaseModel):
    constraint_id: str = Field(default_factory=lambda: str(uuid4()))
    policy_name: str
    source_artifact_id: str
    action: Literal["allow", "block", "require_encryption", "require_review", "pin_region"]
    subject: str
    from_zone: str = ""
    to_zone: str = ""
    data_categories: List[str] = Field(default_factory=list)
    authority_basis: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class OntologySnapshot(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    label: str
    entities: List[OntologyEntity]
    relations: List[OntologyRelation]
    constraints: List[GeometricConstraint]
    zone_cells: Dict[str, List[str]] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class ApiTraceRecord(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    route: str = Field(min_length=1)
    action: str = Field(min_length=1)
    source_region: str = ""
    destination_region: str = ""
    transport_encrypted: bool = True
    data_categories: List[str] = Field(default_factory=list)
    actor: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LiabilitySurfacingRequest(BaseModel):
    snapshot_id: str = Field(min_length=1)
    traces: List[ApiTraceRecord] = Field(min_length=1, max_length=1024)


class LiabilityGap(BaseModel):
    trace_id: str
    route: str
    severity: Literal["low", "medium", "high"]
    violated_constraints: List[str] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    proposed_patch: str


class LiabilitySurfaceResponse(BaseModel):
    snapshot_id: str
    blocked_routes: List[str] = Field(default_factory=list)
    route_scores: Dict[str, float] = Field(default_factory=dict)
    heatmap: List[LiabilityGap] = Field(default_factory=list)
    proposed_patches: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class BiasCategory(BaseModel):
    category_id: str
    stage: str
    label: str
    entry_point: str
    description: str
    signals: List[str] = Field(default_factory=list)


class BiasAssessmentRequest(BaseModel):
    system_name: str = Field(min_length=1)
    active_stages: List[str] = Field(min_length=1)
    observed_signals: List[str] = Field(default_factory=list)
    data_categories: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class BiasFinding(BaseModel):
    category_id: str
    stage: str
    label: str
    severity: Literal["watch", "elevated", "critical"]
    finding: str
    mitigation: str


class BiasAssessmentResponse(BaseModel):
    system_name: str
    total_categories: int = Field(ge=1)
    stage_summary: Dict[str, int] = Field(default_factory=dict)
    findings: List[BiasFinding] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class VerificationArtifact(BaseModel):
    name: str
    status: Literal["present", "missing"]
    detail: str


class VerificationCommand(BaseModel):
    label: str
    command: str


class RuntimeAttestationResponse(BaseModel):
    service: str
    version: str
    environment: str
    openapi_sha256: str
    store_counts: Dict[str, int] = Field(default_factory=dict)
    supported_lanes: List[str] = Field(default_factory=list)
    verification_artifacts: List[VerificationArtifact] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class RuntimeProofBundle(BaseModel):
    service: str
    version: str
    environment: str
    route_count: int = Field(ge=0)
    test_count: int = Field(ge=0)
    verification_artifact_count: int = Field(ge=0)
    connector_kinds: List[str] = Field(default_factory=list)
    supported_lanes: List[str] = Field(default_factory=list)
    store_counts: Dict[str, int] = Field(default_factory=dict)
    verification_commands: List[VerificationCommand] = Field(default_factory=list)
    verification_artifacts: List[VerificationArtifact] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class DatasetField(BaseModel):
    name: str = Field(min_length=1)
    dtype: str = Field(min_length=1)
    nullable: bool = True
    semantic_role: str = ""
    description: str = ""


class DatasetRegistrationRequest(BaseModel):
    dataset_name: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    version: str = Field(min_length=1)
    modality: ModalityKind
    partition_keys: List[str] = Field(default_factory=list)
    primary_keys: List[str] = Field(default_factory=list)
    fields: List[DatasetField] = Field(min_length=1, max_length=512)
    tags: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class DatasetRecord(BaseModel):
    dataset_id: str = Field(default_factory=lambda: str(uuid4()))
    dataset_name: str
    owner: str
    version: str
    modality: ModalityKind
    partition_keys: List[str] = Field(default_factory=list)
    primary_keys: List[str] = Field(default_factory=list)
    fields: List[DatasetField]
    fingerprint: str
    canonical_schema: str
    tags: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class SchemaChange(BaseModel):
    field_name: str
    change_type: Literal["added", "removed", "dtype_changed", "nullability_changed"]
    detail: str


class DatasetEvolutionRequest(BaseModel):
    dataset_name: str = Field(min_length=1)
    candidate_version: str = Field(min_length=1)
    fields: List[DatasetField] = Field(min_length=1, max_length=512)


class DatasetEvolutionResponse(BaseModel):
    dataset_name: str
    current_version: str
    candidate_version: str
    compatible: bool
    additive_changes: List[SchemaChange] = Field(default_factory=list)
    breaking_changes: List[SchemaChange] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


DataClassification = Literal[
    "public",
    "internal",
    "confidential",
    "regulated",
    "restricted",
]
RemovalMode = Literal["delete", "archive", "anonymize", "quarantine"]
LifecycleState = Literal["active", "review_due", "removal_due"]
ChangeSeverity = Literal["low", "medium", "high", "critical"]
ChangeKind = Literal["schema", "connector", "retention", "policy", "model", "serving", "deletion"]
ChangeStatus = Literal["proposed", "approved", "implemented", "reversed"]
SupplyChainNodeKind = Literal[
    "source",
    "connector",
    "dataset",
    "queue",
    "feature_store",
    "model",
    "index",
    "consumer",
    "archive",
    "deletion_lane",
]
SupplyChainMovement = Literal[
    "ingest",
    "normalize",
    "enrich",
    "train",
    "serve",
    "export",
    "archive",
    "delete",
]


class DataLifecyclePolicyRequest(BaseModel):
    dataset_name: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    data_classification: DataClassification = "internal"
    residency_regions: List[str] = Field(default_factory=list, max_length=32)
    allowed_uses: List[str] = Field(default_factory=list, max_length=32)
    effective_from: str = Field(default_factory=utc_now)
    retention_days: int = Field(ge=1, le=36500)
    half_life_days: int = Field(ge=1, le=36500)
    review_interval_days: int = Field(default=30, ge=1, le=3650)
    removal_mode: RemovalMode = "archive"
    deletion_evidence_required: bool = True
    evidence_refs: List[str] = Field(default_factory=list, max_length=64)
    notes: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_schedule(self) -> "DataLifecyclePolicyRequest":
        if self.half_life_days > self.retention_days:
            raise ValueError("half_life_days cannot exceed retention_days")
        return self


class DataLifecyclePolicyRecord(BaseModel):
    policy_id: str = Field(default_factory=lambda: str(uuid4()))
    dataset_id: str
    dataset_name: str
    dataset_version: str
    owner: str
    data_classification: DataClassification
    residency_regions: List[str] = Field(default_factory=list)
    allowed_uses: List[str] = Field(default_factory=list)
    effective_from: str
    retention_days: int = Field(ge=1)
    half_life_days: int = Field(ge=1)
    review_interval_days: int = Field(ge=1)
    half_life_at: str
    next_review_at: str
    removal_due_at: str
    removal_mode: RemovalMode
    deletion_evidence_required: bool = True
    state: LifecycleState
    evidence_refs: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class ChangeControlRequest(BaseModel):
    title: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    change_kind: ChangeKind
    severity: ChangeSeverity = "medium"
    status: ChangeStatus = "proposed"
    summary: str = Field(min_length=1)
    affected_datasets: List[str] = Field(default_factory=list, max_length=64)
    affected_connectors: List[str] = Field(default_factory=list, max_length=64)
    affected_routes: List[str] = Field(default_factory=list, max_length=64)
    linked_policy_ids: List[str] = Field(default_factory=list, max_length=64)
    planned_window: str = ""
    validation_commands: List[str] = Field(default_factory=list, max_length=64)
    rollback_notes: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list, max_length=64)
    notes: List[str] = Field(default_factory=list)


class ChangeControlRecord(BaseModel):
    change_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    owner: str
    change_kind: ChangeKind
    severity: ChangeSeverity
    status: ChangeStatus = "proposed"
    summary: str
    affected_datasets: List[str] = Field(default_factory=list)
    affected_connectors: List[str] = Field(default_factory=list)
    affected_routes: List[str] = Field(default_factory=list)
    linked_policy_ids: List[str] = Field(default_factory=list)
    planned_window: str = ""
    validation_commands: List[str] = Field(default_factory=list)
    rollback_notes: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class SupplyChainNode(BaseModel):
    node_id: str = Field(default_factory=lambda: str(uuid4()))
    label: str = Field(min_length=1)
    node_kind: SupplyChainNodeKind
    dataset_name: str = ""
    owner: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SupplyChainEdge(BaseModel):
    edge_id: str = Field(default_factory=lambda: str(uuid4()))
    from_node_id: str = Field(min_length=1)
    to_node_id: str = Field(min_length=1)
    movement: SupplyChainMovement
    carries_data_categories: List[str] = Field(default_factory=list, max_length=32)
    cross_border: bool = False
    governed: bool = True
    deletion_supported: bool = True
    notes: List[str] = Field(default_factory=list)


class SupplyChainSnapshotRequest(BaseModel):
    label: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    tenant_id: str = ""
    nodes: List[SupplyChainNode] = Field(min_length=1, max_length=256)
    edges: List[SupplyChainEdge] = Field(min_length=1, max_length=512)
    evidence_refs: List[str] = Field(default_factory=list, max_length=64)
    notes: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_nodes(self) -> "SupplyChainSnapshotRequest":
        node_ids = [node.node_id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Supply chain nodes must have unique node ids")
        return self


class SupplyChainSnapshotRecord(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: str(uuid4()))
    label: str
    owner: str
    tenant_id: str = ""
    node_count: int = Field(ge=1)
    edge_count: int = Field(ge=1)
    cross_border_edge_count: int = Field(ge=0)
    governed_edge_count: int = Field(ge=0)
    ungoverned_edge_count: int = Field(ge=0)
    deletion_ready_edge_count: int = Field(ge=0)
    nodes: List[SupplyChainNode]
    edges: List[SupplyChainEdge]
    evidence_refs: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class StewardshipCoverageItem(BaseModel):
    dataset_id: str
    dataset_name: str
    dataset_version: str
    has_policy: bool
    policy_id: str = ""
    data_classification: str = ""
    review_due: bool = False
    removal_due: bool = False
    next_review_at: str = ""
    half_life_at: str = ""
    removal_due_at: str = ""
    notes: List[str] = Field(default_factory=list)


class StewardshipPostureResponse(BaseModel):
    dataset_count: int = Field(ge=0)
    policy_count: int = Field(ge=0)
    covered_dataset_count: int = Field(ge=0)
    uncovered_dataset_count: int = Field(ge=0)
    open_change_controls: int = Field(ge=0)
    approved_change_controls: int = Field(ge=0)
    supply_chain_snapshot_count: int = Field(ge=0)
    cross_border_edge_count: int = Field(ge=0)
    ungoverned_edge_count: int = Field(ge=0)
    deletion_ready_edge_count: int = Field(ge=0)
    datasets: List[StewardshipCoverageItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


ConnectorKind = Literal[
    "local_csv",
    "local_jsonl",
    "local_parquet",
    "s3_parquet",
    "http_json",
    "http_ndjson",
    "web_html",
]


WebExtractMode = Literal["article_blocks", "paragraphs", "headings"]


class WebIngestPolicy(BaseModel):
    user_agent: str = (
        "AdvancedMultimodalAI/0.5 "
        "(public research runtime; repository contact through GitHub)"
    )
    respect_robots: bool = True
    allowed_domains: List[str] = Field(default_factory=list, max_length=64)
    min_interval_ms: int = Field(default=1500, ge=0, le=600000)
    max_bytes: int = Field(default=1_500_000, ge=1024, le=10_000_000)
    extract_mode: WebExtractMode = "article_blocks"
    include_title: bool = True
    include_headings: bool = True

    @field_validator("allowed_domains")
    @classmethod
    def normalize_domains(cls, value: List[str]) -> List[str]:
        normalized: List[str] = []
        seen: set[str] = set()
        for item in value:
            cleaned = item.strip().lower()
            if cleaned.startswith("www."):
                cleaned = cleaned[4:]
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            normalized.append(cleaned)
        return normalized


class WebFetchReceipt(BaseModel):
    url: str
    final_url: str
    domain: str
    status_code: int = Field(ge=0)
    content_type: str = ""
    robots_url: str = ""
    robots_allowed: bool = True
    crawl_delay_seconds: Optional[float] = Field(default=None, ge=0.0)
    request_rate: str = ""
    sitemap_urls: List[str] = Field(default_factory=list)
    bytes_read: int = Field(ge=0)
    extracted_record_count: int = Field(ge=0)
    policy_user_agent: str
    title: str = ""
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class ConnectorConfig(BaseModel):
    kind: ConnectorKind
    source: str = Field(min_length=1)
    records_path: str = ""
    headers_env: Dict[str, str] = Field(default_factory=dict)
    secret_env: Dict[str, str] = Field(default_factory=dict)
    region: str = ""
    endpoint_url: str = ""
    timeout_seconds: float = Field(default=10.0, ge=0.5, le=60.0)
    web_policy: Optional[WebIngestPolicy] = None

    @model_validator(mode="after")
    def validate_shape(self) -> "ConnectorConfig":
        if self.kind != "web_html":
            return self

        parsed = urlparse(self.source)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("web_html connectors require an http or https source URL.")
        if self.headers_env or self.secret_env:
            raise ValueError(
                "web_html connectors are limited to public pages. "
                "Use http_json or http_ndjson for authenticated HTTP sources."
            )
        if self.records_path:
            raise ValueError("web_html connectors do not use records_path.")
        return self


ReadinessState = Literal["pass", "watch", "fail"]
ReadinessPosture = Literal["review_ready", "needs_evidence", "needs_buildout"]


class ReadinessCheck(BaseModel):
    name: str
    state: ReadinessState
    detail: str


class ReadinessBoundary(BaseModel):
    area: str
    detail: str


class ReadinessReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid4()))
    posture: ReadinessPosture
    route_count: int = Field(ge=0)
    test_count: int = Field(ge=0)
    verification_artifact_count: int = Field(ge=0)
    connector_kinds: List[str] = Field(default_factory=list)
    resolved_recipe_count: int = Field(default=0, ge=0)
    compiled_recipe_count: int = Field(default=0, ge=0)
    checks: List[ReadinessCheck] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    boundaries: List[ReadinessBoundary] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class ResearchSurfaceBundle(BaseModel):
    service: str
    version: str
    readiness_posture: ReadinessPosture
    summary: ResearchSurfaceSummary
    lanes: List[ArchitectureLane] = Field(default_factory=list)
    model_cards: List[ModelResearchCard] = Field(default_factory=list)
    findings: List[RepositoryFinding] = Field(default_factory=list)
    connections: List[RepositoryConnection] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class ConnectorBenchmark(BaseModel):
    fetch_ms: float = Field(ge=0.0)
    parse_ms: float = Field(ge=0.0)
    total_ms: float = Field(ge=0.0)
    record_count: int = Field(ge=0)
    bytes_read: int = Field(ge=0)
    rows_per_second: float = Field(ge=0.0)


class ConnectorRegistrationRequest(BaseModel):
    connector: ConnectorConfig
    dataset_name: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    version: str = Field(min_length=1)
    modality: ModalityKind = "tabular"
    partition_keys: List[str] = Field(default_factory=list)
    primary_keys: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    limit: int = Field(default=256, ge=1, le=5000)
    sample_size: int = Field(default=5, ge=1, le=25)


class ConnectorRegistrationResponse(BaseModel):
    dataset: DatasetRecord
    benchmark: ConnectorBenchmark
    record_count: int = Field(ge=0)
    sample_rows: List[Dict[str, Any]] = Field(default_factory=list)


class ConnectorModalityMapping(BaseModel):
    modality: ModalityKind
    feature_fields: List[str] = Field(min_length=1, max_length=256)
    source: str = ""


class ConnectorRunRecord(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    connector_kind: ConnectorKind
    source: str
    dataset_name: str
    record_count: int = Field(ge=0)
    dropped_rows: int = Field(ge=0)
    benchmark: ConnectorBenchmark
    dataset_id: str
    pipeline_run_id: str = ""
    web_receipt: Optional[WebFetchReceipt] = None
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class ConnectorPipelineIngestRequest(BaseModel):
    connector: ConnectorConfig
    dataset_name: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    version: str = Field(min_length=1)
    stream_id: str = Field(min_length=1)
    batch_label: str = "default"
    model_id: str = "adaptive_transformer"
    runtime_mode: RuntimeMode = "contract"
    target: TargetKind = "embedding"
    num_classes: Optional[int] = Field(default=None, ge=2)
    modality_mappings: List[ConnectorModalityMapping] = Field(min_length=1, max_length=12)
    partition_keys: List[str] = Field(default_factory=list)
    primary_keys: List[str] = Field(default_factory=list)
    baseline_label: str = ""
    block_population_drift: bool = True
    limit: int = Field(default=256, ge=1, le=5000)
    sample_size: int = Field(default=5, ge=1, le=25)
    partition_key_field: str = ""
    tags: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    drop_invalid_rows: bool = True


class ConnectorPipelineIngestResponse(BaseModel):
    connector_run: ConnectorRunRecord
    dataset: DatasetRecord
    pipeline_run: PipelineRunRecord


RecipeObjective = Literal[
    "finetune",
    "alignment_eval",
    "retrieval_index",
    "video_cleanup_batch",
    "cross_modal_qa",
]
RecipeAdapterKind = Literal["none", "lora", "qlora", "full_finetune"]
RecipePrecision = Literal["fp32", "fp16", "bf16", "int8", "int4"]
RecipeDistributedEngine = Literal["local", "ddp", "deepspeed", "fsdp"]
RecipeDataSplit = Literal["train", "eval", "test", "predict"]


class RecipeSourceSpec(BaseModel):
    split: RecipeDataSplit = "train"
    modality: ModalityKind
    dataset_name: str = ""
    dataset_version: str = ""
    dataset_id: str = ""
    source_uri: str = ""
    connector_kind: Optional[ConnectorKind] = None
    expected_rows: Optional[int] = Field(default=None, ge=1)
    notes: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_locator(self) -> "RecipeSourceSpec":
        if not any([self.dataset_name, self.dataset_id, self.source_uri]):
            raise ValueError(
                "Recipe sources must provide a dataset name, dataset id, or source URI."
            )
        return self


class RecipeModelSpec(BaseModel):
    model_ref: str = Field(min_length=1)
    family: str = "vision-language"
    context_length: int = Field(default=8192, ge=256, le=262144)
    adapter_kind: RecipeAdapterKind = "lora"
    precision: RecipePrecision = "bf16"
    freeze_vision_tower: bool = True
    freeze_projector: bool = False
    target_modules: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class RecipeTrainingSpec(BaseModel):
    epochs: float = Field(default=1.0, gt=0.0, le=100.0)
    micro_batch_size: int = Field(default=1, ge=1, le=2048)
    gradient_accumulation_steps: int = Field(default=1, ge=1, le=4096)
    learning_rate: float = Field(default=2e-5, gt=0.0, lt=10.0)
    weight_decay: float = Field(default=0.0, ge=0.0, le=10.0)
    warmup_ratio: float = Field(default=0.03, ge=0.0, le=1.0)
    max_steps: int = Field(default=0, ge=0, le=10000000)
    eval_interval_steps: int = Field(default=250, ge=0, le=10000000)
    save_interval_steps: int = Field(default=500, ge=0, le=10000000)
    seed: int = Field(default=42, ge=0)


class RecipeDistributedSpec(BaseModel):
    engine: RecipeDistributedEngine = "local"
    node_count: int = Field(default=1, ge=1, le=256)
    devices_per_node: int = Field(default=1, ge=1, le=64)
    zero_stage: int = Field(default=0, ge=0, le=3)
    gradient_checkpointing: bool = True
    offload_optimizer: bool = False
    launcher_env: Dict[str, str] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_topology(self) -> "RecipeDistributedSpec":
        if self.engine == "local":
            if self.node_count != 1 or self.devices_per_node != 1 or self.zero_stage != 0:
                raise ValueError(
                    "Local recipe execution expects a single node, "
                    "a single device, and ZeRO stage 0."
                )
        elif self.engine != "deepspeed" and self.zero_stage != 0:
            raise ValueError("Only deepspeed recipes may declare a non-zero ZeRO stage.")
        return self


class RecipeEvaluationSpec(BaseModel):
    metrics: List[str] = Field(default_factory=lambda: ["loss"])
    primary_metric: str = "loss"
    minimum_thresholds: Dict[str, float] = Field(default_factory=dict)
    holdout_split: float = Field(default=0.1, ge=0.0, le=0.9)
    latency_budget_ms: Optional[float] = Field(default=None, ge=0.0)
    notes: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_primary_metric(self) -> "RecipeEvaluationSpec":
        if self.metrics and self.primary_metric not in self.metrics:
            raise ValueError("The primary metric must appear in the metrics list.")
        return self


class RecipeCompileRequest(BaseModel):
    label: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    objective: RecipeObjective = "finetune"
    model: RecipeModelSpec
    sources: List[RecipeSourceSpec] = Field(min_length=1, max_length=32)
    training: RecipeTrainingSpec = Field(default_factory=RecipeTrainingSpec)
    distributed: RecipeDistributedSpec = Field(default_factory=RecipeDistributedSpec)
    evaluation: RecipeEvaluationSpec = Field(default_factory=RecipeEvaluationSpec)
    tags: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class RecipeDatasetResolution(BaseModel):
    split: RecipeDataSplit
    modality: ModalityKind
    dataset_id: str = ""
    dataset_name: str = ""
    version: str = ""
    resolved: bool
    field_count: int = Field(default=0, ge=0)
    primary_keys: List[str] = Field(default_factory=list)
    partition_keys: List[str] = Field(default_factory=list)
    source_uri: str = ""
    connector_kind: Optional[ConnectorKind] = None
    notes: List[str] = Field(default_factory=list)


class RecipeLaunchCommand(BaseModel):
    label: str
    command: str
    verified: bool = True


class RecipeLaunchProfile(BaseModel):
    launcher: Literal["python", "torchrun"]
    engine: RecipeDistributedEngine
    node_count: int = Field(ge=1)
    devices_per_node: int = Field(ge=1)
    estimated_global_batch_size: int = Field(ge=1)
    verified_commands: List[RecipeLaunchCommand] = Field(default_factory=list)
    launcher_template: str = ""
    artifacts: List[str] = Field(default_factory=list)
    environment: Dict[str, str] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)


class RecipeRecord(BaseModel):
    recipe_id: str = Field(default_factory=lambda: str(uuid4()))
    label: str
    owner: str
    objective: RecipeObjective
    model: RecipeModelSpec
    sources: List[RecipeSourceSpec]
    training: RecipeTrainingSpec
    distributed: RecipeDistributedSpec
    evaluation: RecipeEvaluationSpec
    resolved_sources: List[RecipeDatasetResolution] = Field(default_factory=list)
    launch_profile: Optional[RecipeLaunchProfile] = None
    proof_obligations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
