from __future__ import annotations

import asyncio

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response, WebSocket

from .config import get_settings
from .contracts import (
    BatchInferenceRequest,
    BiasAssessmentRequest,
    ConnectorPipelineIngestRequest,
    ConnectorRegistrationRequest,
    DatasetEvolutionRequest,
    DatasetRegistrationRequest,
    DriftBaselineRequest,
    InferenceRequest,
    LiabilitySurfacingRequest,
    OntologyIngestRequest,
    PipelineIngestRequest,
    PopulationDriftRequest,
    RecipeCompileRequest,
    RetrievalQueryRequest,
    RetrievalUpsertRequest,
    TemporalAlignmentRequest,
    VideoCleaningRequest,
    VideoPacketRequest,
)
from .observability import render_metrics
from .service import AdvancedMultimodalService, PopulationDriftBlockedError


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

    @app.get("/v1/proof/bundle")
    def runtime_proof_bundle():
        runtime_routes = [
            route
            for route in app.routes
            if getattr(route, "path", "").startswith("/v1/")
            or getattr(route, "path", "") in {"/", "/metrics"}
        ]
        return service.runtime_proof_bundle(route_count=len(runtime_routes))

    @app.get("/v1/readiness/report")
    def readiness_report():
        runtime_routes = [
            route
            for route in app.routes
            if getattr(route, "path", "").startswith("/v1/")
            or getattr(route, "path", "") in {"/", "/metrics"}
        ]
        return service.readiness_report(route_count=len(runtime_routes))

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

    @app.get("/metrics")
    def metrics():
        payload, content_type = render_metrics()
        return Response(content=payload, media_type=content_type)

    return app
