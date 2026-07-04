from __future__ import annotations

import asyncio

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response, WebSocket

from .config import get_settings
from .contracts import (
    BatchInferenceRequest,
    BiasAssessmentRequest,
    ChangeControlRequest,
    ComplianceLedgerToken,
    ConnectorPipelineIngestRequest,
    ConnectorRegistrationRequest,
    CymaticSurfaceBundle,
    DataLifecyclePolicyRequest,
    DatasetEvolutionRequest,
    DatasetRegistrationRequest,
    DeliberationAssessmentRequest,
    DeliberationAssessmentResponse,
    DriftBaselineRequest,
    EdgeGatewayTopology,
    EdgePacketEvaluationResponse,
    EdgePacketRequest,
    EdgeTrackingLedgerSummary,
    EpistemicRiskRequest,
    EpistemicRiskResponse,
    HarnessImprovementRequest,
    HarnessImprovementResponse,
    IndustrialDiagnosticRequest,
    IndustrialDiagnosticResponse,
    IndustrialModelCheckRequest,
    IndustrialModelCheckResponse,
    IndustrialScenarioBundle,
    IndustryProfileBundle,
    InferenceRequest,
    LiabilitySurfacingRequest,
    MusicFeatureExtractionRequest,
    MusicTrackManifestRequest,
    OntologyIngestRequest,
    OperatorSurfaceBundle,
    PipelineIngestRequest,
    PopulationDriftRequest,
    RecipeCompileRequest,
    ReferenceBenchmarkRequest,
    RepositoryGrowthSnapshot,
    ResearchInfluenceBundle,
    RetrievalQueryRequest,
    RetrievalUpsertRequest,
    SupplyChainSnapshotRequest,
    TemporalAlignmentRequest,
    TrustCalibrationRequest,
    TrustCalibrationResponse,
    VideoCleaningRequest,
    VideoPacketRequest,
)
from .observability import render_metrics
from .service import (
    AdvancedMultimodalService,
    PopulationDriftBlockedError,
    TensorInterceptBlockedError,
)


def create_app() -> FastAPI:
    settings = get_settings()
    service = AdvancedMultimodalService(settings)
    app = FastAPI(
        title="Advanced Multi-modal AI",
        version=settings.service_version,
        summary=(
            "A multimodal runtime surface for orchestration, retrieval, "
            "quality profiling, provenance, temporal alignment, "
            "public-web intake, and video evidence planning."
        ),
    )
    app.state.service = service

    @app.middleware("http")
    async def emit_compliance_ledger_token(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/v1/"):
            ledger_token = service.compliance_ledger_token(
                route=request.url.path,
                method=request.method,
                status_code=response.status_code,
            )
            response.headers["X-AMAI-Ledger-Token"] = ledger_token.token_id
            response.headers["X-AMAI-Ledger-Scope"] = ledger_token.governance_scope
            response.headers["X-AMAI-Ledger-Lanes"] = ",".join(ledger_token.governance_lanes)
            response.headers["X-AMAI-Ledger-OpenAPI"] = ledger_token.openapi_sha256
            response.headers["X-AMAI-Ledger-Stores"] = ledger_token.store_counts_hash
            response.headers["X-AMAI-Ledger-Payload"] = ledger_token.compact_payload
        return response

    @app.get("/")
    def root():
        return {
            "service": settings.service_name,
            "version": settings.service_version,
            "docs": "/docs",
            "theme": settings.repository_theme,
        }

    @app.get("/v1/health")
    def health():
        return service.health()

    @app.get("/v1/ready")
    def ready():
        return {
            "status": service.health().status,
            "models": len(service.list_models()),
            "retrieval_backend": service.vector_index.backend,
        }

    @app.get("/v1/models")
    def models():
        return service.list_models()

    @app.get("/v1/research/models")
    def research_models():
        return service.list_model_research_cards()

    @app.get("/v1/research/findings")
    def research_findings():
        return service.research_surface_bundle(route_count=_runtime_route_count(app)).findings

    @app.get("/v1/research/connections")
    def research_connections():
        return service.research_surface_bundle(route_count=_runtime_route_count(app)).connections

    @app.get("/v1/research/surfaces")
    def research_surfaces():
        return service.research_surface_bundle(route_count=_runtime_route_count(app))

    @app.get("/v1/research/cymatic-surface")
    def research_cymatic_surface() -> CymaticSurfaceBundle:
        return service.cymatic_surface_bundle(route_count=_runtime_route_count(app))

    @app.get("/v1/research/influence")
    def research_influence() -> ResearchInfluenceBundle:
        return service.research_influence_bundle(route_count=_runtime_route_count(app))

    @app.post("/v1/research/harness-improvement")
    def research_harness_improvement(
        request: HarnessImprovementRequest,
    ) -> HarnessImprovementResponse:
        return service.mine_harness_improvements(request)

    @app.post("/v1/research/deliberation/assess")
    def research_deliberation_assessment(
        request: DeliberationAssessmentRequest,
    ) -> DeliberationAssessmentResponse:
        return service.assess_research_deliberation(request)

    @app.post("/v1/research/trust/calibrate")
    def research_trust_calibration(
        request: TrustCalibrationRequest,
    ) -> TrustCalibrationResponse:
        return service.calibrate_research_trust(request)

    @app.post("/v1/research/epistemic-risk/assess")
    def research_epistemic_risk(
        request: EpistemicRiskRequest,
    ) -> EpistemicRiskResponse:
        return service.assess_research_epistemic_risk(request)

    @app.get("/v1/operators/surfaces")
    def operator_surfaces() -> OperatorSurfaceBundle:
        return service.operator_surface_bundle(route_count=_runtime_route_count(app))

    @app.get("/v1/operators/commands")
    def operator_commands():
        return service.operator_surface_bundle(route_count=_runtime_route_count(app)).commands

    @app.get("/v1/operators/skills")
    def operator_skills():
        return service.operator_surface_bundle(route_count=_runtime_route_count(app)).skills

    @app.get("/v1/operators/plugins")
    def operator_plugins():
        return service.operator_surface_bundle(route_count=_runtime_route_count(app)).plugins

    @app.get("/v1/operators/speech-tasks")
    def operator_speech_tasks():
        return service.operator_surface_bundle(route_count=_runtime_route_count(app)).speech_tasks

    @app.get("/v1/music/overview")
    def music_overview(limit: int = 6):
        return service.music_overview(limit=limit)

    @app.get("/v1/music/snapshot")
    def music_snapshot(limit: int = 12):
        return service.music_snapshot(limit=limit)

    @app.post("/v1/music/manifests")
    def register_music_manifest(request: MusicTrackManifestRequest):
        return service.register_music_manifest(request)

    @app.get("/v1/music/manifests")
    def list_music_manifests(limit: int = 50):
        return service.list_music_manifests(limit=limit)

    @app.get("/v1/music/manifests/{manifest_id}")
    def get_music_manifest(manifest_id: str):
        record = service.get_music_manifest(manifest_id)
        if record is None:
            raise HTTPException(status_code=404, detail="music manifest not found")
        return record

    @app.post("/v1/music/features/extract")
    def extract_music_features(request: MusicFeatureExtractionRequest):
        try:
            return service.extract_music_features(request)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/v1/music/features/runs")
    def list_music_feature_runs(limit: int = 50):
        return service.list_music_feature_runs(limit=limit)

    @app.get("/v1/music/features/runs/{run_id}")
    def get_music_feature_run(run_id: str):
        record = service.get_music_feature_run(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="music feature run not found")
        return record

    @app.get("/v1/music/features/query")
    def query_music_feature_rows(limit: int = 32, manifest_id: str = "", run_id: str = ""):
        return service.music_feature_slice(limit=limit, manifest_id=manifest_id, run_id=run_id)

    @app.get("/v1/music/segments")
    def list_music_segments(limit: int = 48, manifest_id: str = "", run_id: str = ""):
        return service.list_music_segments(limit=limit, manifest_id=manifest_id, run_id=run_id)

    @app.get("/v1/music/alignment")
    def music_alignment(run_id: str = ""):
        return service.music_alignment_preview(run_id=run_id)

    @app.get("/v1/music/drift")
    def music_drift(limit: int = 12):
        return service.music_drift_report(limit=limit)

    @app.get("/v1/music/proof/change-report")
    def music_change_proof(limit: int = 12):
        return service.music_change_proof(limit=limit)

    @app.get("/v1/industries/profiles")
    def industry_profiles() -> IndustryProfileBundle:
        return service.industry_profile_bundle()

    @app.get("/v1/industrial/scenarios")
    def industrial_scenarios() -> IndustrialScenarioBundle:
        return service.industrial_scenarios()

    @app.post("/v1/industrial/diagnose")
    def industrial_diagnose(
        request: IndustrialDiagnosticRequest,
    ) -> IndustrialDiagnosticResponse:
        return service.industrial_diagnose(request)

    @app.post("/v1/industrial/model-check")
    def industrial_model_check(
        request: IndustrialModelCheckRequest,
    ) -> IndustrialModelCheckResponse:
        return service.industrial_model_check(request)

    @app.get("/v1/repository/pulse")
    def repository_pulse():
        return service.repository_pulse(route_count=_runtime_route_count(app))

    @app.get("/v1/growth/snapshot")
    def repository_growth_snapshot() -> RepositoryGrowthSnapshot:
        return service.repository_growth_snapshot(route_count=_runtime_route_count(app))

    @app.get("/v1/execution/journal")
    def execution_journal(limit: int = 20):
        return service.execution_journal(limit=limit)

    @app.post("/v1/edge/evaluate")
    def edge_evaluate(request: EdgePacketRequest) -> EdgePacketEvaluationResponse:
        return service.evaluate_edge_packet(request)

    @app.get("/v1/edge/ledger")
    def edge_ledger(limit: int = 20) -> EdgeTrackingLedgerSummary:
        return service.edge_tracking_ledger(limit=limit)

    @app.get("/v1/edge/topology")
    def edge_topology() -> EdgeGatewayTopology:
        return service.edge_gateway_topology(route_count=_runtime_route_count(app))

    @app.post("/v1/catalog/register")
    def register_dataset(request: DatasetRegistrationRequest):
        return service.register_dataset(request)

    @app.get("/v1/catalog/datasets")
    def list_datasets(limit: int = 100):
        return service.list_datasets(limit=limit)

    @app.get("/v1/catalog/datasets/{dataset_id}")
    def get_dataset(dataset_id: str):
        record = service.get_dataset(dataset_id)
        if record is None:
            raise HTTPException(status_code=404, detail="dataset not found")
        return record

    @app.post("/v1/catalog/evolution")
    def compare_dataset_evolution(request: DatasetEvolutionRequest):
        try:
            return service.compare_dataset_evolution(request)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/v1/stewardship/lifecycle")
    def register_lifecycle_policy(request: DataLifecyclePolicyRequest):
        try:
            return service.register_lifecycle_policy(request)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/v1/stewardship/lifecycle")
    def list_lifecycle_policies(limit: int = 100):
        return service.list_lifecycle_policies(limit=limit)

    @app.get("/v1/stewardship/lifecycle/{policy_id}")
    def get_lifecycle_policy(policy_id: str):
        record = service.get_lifecycle_policy(policy_id)
        if record is None:
            raise HTTPException(status_code=404, detail="lifecycle policy not found")
        return record

    @app.post("/v1/stewardship/change-controls")
    def create_change_control(request: ChangeControlRequest):
        try:
            return service.create_change_control(request)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/v1/stewardship/change-controls")
    def list_change_controls(limit: int = 100):
        return service.list_change_controls(limit=limit)

    @app.get("/v1/stewardship/change-controls/{change_id}")
    def get_change_control(change_id: str):
        record = service.get_change_control(change_id)
        if record is None:
            raise HTTPException(status_code=404, detail="change control not found")
        return record

    @app.post("/v1/stewardship/supply-chain")
    def create_supply_chain_snapshot(request: SupplyChainSnapshotRequest):
        try:
            return service.create_supply_chain_snapshot(request)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/v1/stewardship/supply-chain")
    def list_supply_chain_snapshots(limit: int = 100):
        return service.list_supply_chain_snapshots(limit=limit)

    @app.get("/v1/stewardship/supply-chain/{snapshot_id}")
    def get_supply_chain_snapshot(snapshot_id: str):
        record = service.get_supply_chain_snapshot(snapshot_id)
        if record is None:
            raise HTTPException(status_code=404, detail="supply-chain snapshot not found")
        return record

    @app.get("/v1/stewardship/posture")
    def stewardship_posture():
        return service.stewardship_posture()

    @app.post("/v1/connectors/register")
    def register_connector_dataset(request: ConnectorRegistrationRequest):
        try:
            return service.register_connector_dataset(request)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/v1/connectors/pipeline-ingest")
    def connector_pipeline_ingest(request: ConnectorPipelineIngestRequest):
        try:
            return service.connector_pipeline_ingest(request)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/v1/connectors/runs")
    def list_connector_runs(limit: int = 50):
        return service.list_connector_runs(limit=limit)

    @app.get("/v1/connectors/runs/{run_id}")
    def get_connector_run(run_id: str):
        record = service.get_connector_run(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="connector run not found")
        return record

    @app.get("/v1/runtime/attestation")
    def runtime_attestation():
        return service.runtime_attestation()

    @app.get("/v1/runtime/compliance-ledger")
    def runtime_compliance_ledger(
        route: str = "/v1/infer",
        method: str = "POST",
        status_code: int = 200,
    ) -> ComplianceLedgerToken:
        return service.compliance_ledger_token(
            route=route,
            method=method,
            status_code=status_code,
        )

    @app.get("/v1/proof/bundle")
    def runtime_proof_bundle():
        return service.runtime_proof_bundle(route_count=_runtime_route_count(app))

    @app.get("/v1/readiness/report")
    def readiness_report():
        return service.readiness_report(route_count=_runtime_route_count(app))

    @app.get("/v1/bias/taxonomy")
    def bias_taxonomy():
        return service.list_bias_taxonomy()

    @app.post("/v1/bias/assess")
    def bias_assessment(request: BiasAssessmentRequest):
        return service.assess_bias(request)

    @app.post("/v1/plan")
    def plan(request: InferenceRequest):
        return service.plan(request)

    @app.post("/v1/recipes/compile")
    def compile_recipe(request: RecipeCompileRequest):
        return service.compile_recipe(request)

    @app.get("/v1/recipes")
    def list_recipes(limit: int = 100):
        return service.list_recipes(limit=limit)

    @app.get("/v1/recipes/{recipe_id}")
    def get_recipe(recipe_id: str):
        record = service.get_recipe(recipe_id)
        if record is None:
            raise HTTPException(status_code=404, detail="recipe not found")
        return record

    @app.post("/v1/data/profile")
    def data_profile(request: InferenceRequest):
        return service.profile_request(request)

    @app.post("/v1/data/intercept")
    def data_intercept(request: InferenceRequest):
        return service.inspect_tensor_request(request)

    @app.post("/v1/data/provenance")
    def data_provenance(request: InferenceRequest):
        return service.build_provenance(request)

    @app.post("/v1/alignment/windows")
    def alignment_windows(request: TemporalAlignmentRequest):
        return service.align_temporal_observations(request)

    @app.post("/v1/drift/baselines")
    def create_drift_baseline(request: DriftBaselineRequest):
        return service.create_drift_baseline(request)

    @app.get("/v1/drift/baselines")
    def list_drift_baselines(limit: int = 50):
        return service.list_drift_baselines(limit=limit)

    @app.post("/v1/drift/check")
    def population_drift_check(request: PopulationDriftRequest):
        try:
            return service.check_population_drift(request)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/v1/pipelines/ingest")
    def pipeline_ingest(request: PipelineIngestRequest):
        try:
            return service.ingest_pipeline_batch(request)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.get("/v1/pipelines/runs")
    def list_pipeline_runs(limit: int = 50):
        return service.list_pipeline_runs(limit=limit)

    @app.get("/v1/pipelines/runs/{run_id}")
    def get_pipeline_run(run_id: str):
        record = service.get_pipeline_run(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="pipeline run not found")
        return record

    @app.get("/v1/pipelines/runs/{run_id}/export")
    def export_pipeline_run(run_id: str):
        record = service.export_pipeline_run(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="pipeline run not found")
        return record

    @app.post("/v1/pipelines/runs/{run_id}/replay")
    def replay_pipeline_run(run_id: str):
        record = service.replay_pipeline_run(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="pipeline run not found")
        return record

    @app.post("/v1/ontology/ingest")
    def ontology_ingest(request: OntologyIngestRequest):
        return service.ingest_ontology(request)

    @app.get("/v1/ontology/snapshots")
    def list_ontology_snapshots(limit: int = 50):
        return service.list_ontology_snapshots(limit=limit)

    @app.get("/v1/ontology/snapshots/{snapshot_id}")
    def get_ontology_snapshot(snapshot_id: str):
        record = service.get_ontology_snapshot(snapshot_id)
        if record is None:
            raise HTTPException(status_code=404, detail="ontology snapshot not found")
        return record

    @app.post("/v1/ontology/liability")
    def ontology_liability(request: LiabilitySurfacingRequest):
        try:
            return service.surface_liability(request)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/v1/infer")
    def infer(request: InferenceRequest):
        try:
            return service.infer(request)
        except TensorInterceptBlockedError as error:
            raise HTTPException(
                status_code=422,
                detail=error.response.model_dump(mode="json"),
            ) from error
        except PopulationDriftBlockedError as error:
            raise HTTPException(
                status_code=409,
                detail=error.response.model_dump(mode="json"),
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @app.post("/v1/jobs/video-clean")
    def enqueue_video_clean(
        request: VideoCleaningRequest,
        background_tasks: BackgroundTasks,
    ):
        submission = service.submit_video_clean_job(request)
        background_tasks.add_task(service.run_video_clean_job, submission.job_id, request)
        return submission

    @app.post("/v1/jobs/batch-infer")
    def enqueue_batch_infer(
        request: BatchInferenceRequest,
        background_tasks: BackgroundTasks,
    ):
        submission = service.submit_batch_inference_job(request)
        background_tasks.add_task(service.run_batch_inference_job, submission.job_id, request)
        return submission

    @app.get("/v1/jobs")
    def list_jobs(limit: int = 20):
        return service.list_jobs(limit=limit)

    @app.get("/v1/jobs/{job_id}")
    def get_job(job_id: str):
        record = service.get_job(job_id)
        if record is None:
            raise HTTPException(status_code=404, detail="job not found")
        return record

    @app.websocket("/v1/stream")
    async def stream(websocket: WebSocket):
        await websocket.accept()
        raw_payload = await websocket.receive_json()
        try:
            request = InferenceRequest.model_validate(raw_payload)
            for event in service.stream_inference_events(request):
                await websocket.send_json(event)
                if settings.stream_event_delay_ms:
                    await asyncio.sleep(settings.stream_event_delay_ms / 1000)
        except TensorInterceptBlockedError as error:
            await websocket.send_json(
                {"event": "blocked", "payload": error.response.model_dump(mode="json")}
            )
            await websocket.close()
            return
        except PopulationDriftBlockedError as error:
            await websocket.send_json(
                {"event": "blocked", "payload": error.response.model_dump(mode="json")}
            )
            await websocket.close()
            return
        except ValueError as error:
            await websocket.send_json({"event": "error", "detail": str(error)})
            await websocket.close()
            return
        await websocket.close()

    @app.post("/v1/retrieval/upsert")
    def retrieval_upsert(request: RetrievalUpsertRequest):
        return service.upsert_retrieval_records(request)

    @app.post("/v1/retrieval/query")
    def retrieval_query(request: RetrievalQueryRequest):
        return service.query_retrieval(request)

    @app.post("/v1/video/packet")
    def video_packet(request: VideoPacketRequest):
        return service.build_video_packet(request)

    @app.post("/v1/video/clean")
    def video_clean(request: VideoCleaningRequest):
        return service.clean_video_packet(request)

    @app.get("/v1/benchmarks/smoke")
    def smoke_benchmark(model_id: str = "adaptive_transformer", iterations: int = 10):
        return service.run_smoke_benchmark(model_id=model_id, iterations=iterations)

    @app.get("/v1/benchmarks/reference")
    def reference_benchmark_default():
        return service.run_reference_benchmark(route_count=_runtime_route_count(app))

    @app.post("/v1/benchmarks/reference")
    def reference_benchmark(request: ReferenceBenchmarkRequest):
        return service.run_reference_benchmark(
            route_count=_runtime_route_count(app),
            request=request,
        )

    @app.get("/metrics")
    def metrics():
        payload, content_type = render_metrics()
        return Response(content=payload, media_type=content_type)

    return app


def _runtime_route_count(app: FastAPI) -> int:
    runtime_routes = [
        route
        for route in app.routes
        if getattr(route, "path", "").startswith("/v1/")
        or getattr(route, "path", "") in {"/", "/metrics"}
    ]
    return len(runtime_routes)
