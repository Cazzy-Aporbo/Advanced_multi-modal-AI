"""Generated from openapi/openapi.json. Do not edit by hand."""

from __future__ import annotations

from typing import Any

import httpx


class GeneratedOpenAPIClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        payload: Any | None = None,
    ) -> Any:
        response = httpx.request(
            method=method,
            url=f"{self.base_url}{path}",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def rootGet(self) -> Any:
        """Root"""
        path = f"/"
        return self._request("GET", path)

    def healthV1HealthGet(self) -> Any:
        """Health"""
        path = f"/v1/health"
        return self._request("GET", path)

    def readyV1ReadyGet(self) -> Any:
        """Ready"""
        path = f"/v1/ready"
        return self._request("GET", path)

    def modelsV1ModelsGet(self) -> Any:
        """Models"""
        path = f"/v1/models"
        return self._request("GET", path)

    def researchModelsV1ResearchModelsGet(self) -> Any:
        """Research Models"""
        path = f"/v1/research/models"
        return self._request("GET", path)

    def researchFindingsV1ResearchFindingsGet(self) -> Any:
        """Research Findings"""
        path = f"/v1/research/findings"
        return self._request("GET", path)

    def researchConnectionsV1ResearchConnectionsGet(self) -> Any:
        """Research Connections"""
        path = f"/v1/research/connections"
        return self._request("GET", path)

    def researchSurfacesV1ResearchSurfacesGet(self) -> Any:
        """Research Surfaces"""
        path = f"/v1/research/surfaces"
        return self._request("GET", path)

    def repositoryPulseV1RepositoryPulseGet(self) -> Any:
        """Repository Pulse"""
        path = f"/v1/repository/pulse"
        return self._request("GET", path)

    def executionJournalV1ExecutionJournalGet(self, query: dict[str, str | int | float | bool] | None = None) -> Any:
        """Execution Journal"""
        path = f"/v1/execution/journal"
        if query:
            encoded = httpx.QueryParams(query)
            path = f"{path}?{encoded}"
        return self._request("GET", path)

    def registerDatasetV1CatalogRegisterPost(self, payload: Any) -> Any:
        """Register Dataset"""
        path = f"/v1/catalog/register"
        return self._request("POST", path, payload=payload)

    def listDatasetsV1CatalogDatasetsGet(self, query: dict[str, str | int | float | bool] | None = None) -> Any:
        """List Datasets"""
        path = f"/v1/catalog/datasets"
        if query:
            encoded = httpx.QueryParams(query)
            path = f"{path}?{encoded}"
        return self._request("GET", path)

    def getDatasetV1CatalogDatasetsDatasetIdGet(self, dataset_id: str | int) -> Any:
        """Get Dataset"""
        path = f"/v1/catalog/datasets/{dataset_id}"
        return self._request("GET", path)

    def compareDatasetEvolutionV1CatalogEvolutionPost(self, payload: Any) -> Any:
        """Compare Dataset Evolution"""
        path = f"/v1/catalog/evolution"
        return self._request("POST", path, payload=payload)

    def listLifecyclePoliciesV1StewardshipLifecycleGet(self, query: dict[str, str | int | float | bool] | None = None) -> Any:
        """List Lifecycle Policies"""
        path = f"/v1/stewardship/lifecycle"
        if query:
            encoded = httpx.QueryParams(query)
            path = f"{path}?{encoded}"
        return self._request("GET", path)

    def registerLifecyclePolicyV1StewardshipLifecyclePost(self, payload: Any) -> Any:
        """Register Lifecycle Policy"""
        path = f"/v1/stewardship/lifecycle"
        return self._request("POST", path, payload=payload)

    def getLifecyclePolicyV1StewardshipLifecyclePolicyIdGet(self, policy_id: str | int) -> Any:
        """Get Lifecycle Policy"""
        path = f"/v1/stewardship/lifecycle/{policy_id}"
        return self._request("GET", path)

    def listChangeControlsV1StewardshipChangeControlsGet(self, query: dict[str, str | int | float | bool] | None = None) -> Any:
        """List Change Controls"""
        path = f"/v1/stewardship/change-controls"
        if query:
            encoded = httpx.QueryParams(query)
            path = f"{path}?{encoded}"
        return self._request("GET", path)

    def createChangeControlV1StewardshipChangeControlsPost(self, payload: Any) -> Any:
        """Create Change Control"""
        path = f"/v1/stewardship/change-controls"
        return self._request("POST", path, payload=payload)

    def getChangeControlV1StewardshipChangeControlsChangeIdGet(self, change_id: str | int) -> Any:
        """Get Change Control"""
        path = f"/v1/stewardship/change-controls/{change_id}"
        return self._request("GET", path)

    def listSupplyChainSnapshotsV1StewardshipSupplyChainGet(self, query: dict[str, str | int | float | bool] | None = None) -> Any:
        """List Supply Chain Snapshots"""
        path = f"/v1/stewardship/supply-chain"
        if query:
            encoded = httpx.QueryParams(query)
            path = f"{path}?{encoded}"
        return self._request("GET", path)

    def createSupplyChainSnapshotV1StewardshipSupplyChainPost(self, payload: Any) -> Any:
        """Create Supply Chain Snapshot"""
        path = f"/v1/stewardship/supply-chain"
        return self._request("POST", path, payload=payload)

    def getSupplyChainSnapshotV1StewardshipSupplyChainSnapshotIdGet(self, snapshot_id: str | int) -> Any:
        """Get Supply Chain Snapshot"""
        path = f"/v1/stewardship/supply-chain/{snapshot_id}"
        return self._request("GET", path)

    def stewardshipPostureV1StewardshipPostureGet(self) -> Any:
        """Stewardship Posture"""
        path = f"/v1/stewardship/posture"
        return self._request("GET", path)

    def registerConnectorDatasetV1ConnectorsRegisterPost(self, payload: Any) -> Any:
        """Register Connector Dataset"""
        path = f"/v1/connectors/register"
        return self._request("POST", path, payload=payload)

    def connectorPipelineIngestV1ConnectorsPipelineIngestPost(self, payload: Any) -> Any:
        """Connector Pipeline Ingest"""
        path = f"/v1/connectors/pipeline-ingest"
        return self._request("POST", path, payload=payload)

    def listConnectorRunsV1ConnectorsRunsGet(self, query: dict[str, str | int | float | bool] | None = None) -> Any:
        """List Connector Runs"""
        path = f"/v1/connectors/runs"
        if query:
            encoded = httpx.QueryParams(query)
            path = f"{path}?{encoded}"
        return self._request("GET", path)

    def getConnectorRunV1ConnectorsRunsRunIdGet(self, run_id: str | int) -> Any:
        """Get Connector Run"""
        path = f"/v1/connectors/runs/{run_id}"
        return self._request("GET", path)

    def runtimeAttestationV1RuntimeAttestationGet(self) -> Any:
        """Runtime Attestation"""
        path = f"/v1/runtime/attestation"
        return self._request("GET", path)

    def runtimeProofBundleV1ProofBundleGet(self) -> Any:
        """Runtime Proof Bundle"""
        path = f"/v1/proof/bundle"
        return self._request("GET", path)

    def readinessReportV1ReadinessReportGet(self) -> Any:
        """Readiness Report"""
        path = f"/v1/readiness/report"
        return self._request("GET", path)

    def biasTaxonomyV1BiasTaxonomyGet(self) -> Any:
        """Bias Taxonomy"""
        path = f"/v1/bias/taxonomy"
        return self._request("GET", path)

    def biasAssessmentV1BiasAssessPost(self, payload: Any) -> Any:
        """Bias Assessment"""
        path = f"/v1/bias/assess"
        return self._request("POST", path, payload=payload)

    def planV1PlanPost(self, payload: Any) -> Any:
        """Plan"""
        path = f"/v1/plan"
        return self._request("POST", path, payload=payload)

    def compileRecipeV1RecipesCompilePost(self, payload: Any) -> Any:
        """Compile Recipe"""
        path = f"/v1/recipes/compile"
        return self._request("POST", path, payload=payload)

    def listRecipesV1RecipesGet(self, query: dict[str, str | int | float | bool] | None = None) -> Any:
        """List Recipes"""
        path = f"/v1/recipes"
        if query:
            encoded = httpx.QueryParams(query)
            path = f"{path}?{encoded}"
        return self._request("GET", path)

    def getRecipeV1RecipesRecipeIdGet(self, recipe_id: str | int) -> Any:
        """Get Recipe"""
        path = f"/v1/recipes/{recipe_id}"
        return self._request("GET", path)

    def dataProfileV1DataProfilePost(self, payload: Any) -> Any:
        """Data Profile"""
        path = f"/v1/data/profile"
        return self._request("POST", path, payload=payload)

    def dataInterceptV1DataInterceptPost(self, payload: Any) -> Any:
        """Data Intercept"""
        path = f"/v1/data/intercept"
        return self._request("POST", path, payload=payload)

    def dataProvenanceV1DataProvenancePost(self, payload: Any) -> Any:
        """Data Provenance"""
        path = f"/v1/data/provenance"
        return self._request("POST", path, payload=payload)

    def alignmentWindowsV1AlignmentWindowsPost(self, payload: Any) -> Any:
        """Alignment Windows"""
        path = f"/v1/alignment/windows"
        return self._request("POST", path, payload=payload)

    def listDriftBaselinesV1DriftBaselinesGet(self, query: dict[str, str | int | float | bool] | None = None) -> Any:
        """List Drift Baselines"""
        path = f"/v1/drift/baselines"
        if query:
            encoded = httpx.QueryParams(query)
            path = f"{path}?{encoded}"
        return self._request("GET", path)

    def createDriftBaselineV1DriftBaselinesPost(self, payload: Any) -> Any:
        """Create Drift Baseline"""
        path = f"/v1/drift/baselines"
        return self._request("POST", path, payload=payload)

    def populationDriftCheckV1DriftCheckPost(self, payload: Any) -> Any:
        """Population Drift Check"""
        path = f"/v1/drift/check"
        return self._request("POST", path, payload=payload)

    def pipelineIngestV1PipelinesIngestPost(self, payload: Any) -> Any:
        """Pipeline Ingest"""
        path = f"/v1/pipelines/ingest"
        return self._request("POST", path, payload=payload)

    def listPipelineRunsV1PipelinesRunsGet(self, query: dict[str, str | int | float | bool] | None = None) -> Any:
        """List Pipeline Runs"""
        path = f"/v1/pipelines/runs"
        if query:
            encoded = httpx.QueryParams(query)
            path = f"{path}?{encoded}"
        return self._request("GET", path)

    def getPipelineRunV1PipelinesRunsRunIdGet(self, run_id: str | int) -> Any:
        """Get Pipeline Run"""
        path = f"/v1/pipelines/runs/{run_id}"
        return self._request("GET", path)

    def exportPipelineRunV1PipelinesRunsRunIdExportGet(self, run_id: str | int) -> Any:
        """Export Pipeline Run"""
        path = f"/v1/pipelines/runs/{run_id}/export"
        return self._request("GET", path)

    def replayPipelineRunV1PipelinesRunsRunIdReplayPost(self, run_id: str | int) -> Any:
        """Replay Pipeline Run"""
        path = f"/v1/pipelines/runs/{run_id}/replay"
        return self._request("POST", path)

    def ontologyIngestV1OntologyIngestPost(self, payload: Any) -> Any:
        """Ontology Ingest"""
        path = f"/v1/ontology/ingest"
        return self._request("POST", path, payload=payload)

    def listOntologySnapshotsV1OntologySnapshotsGet(self, query: dict[str, str | int | float | bool] | None = None) -> Any:
        """List Ontology Snapshots"""
        path = f"/v1/ontology/snapshots"
        if query:
            encoded = httpx.QueryParams(query)
            path = f"{path}?{encoded}"
        return self._request("GET", path)

    def getOntologySnapshotV1OntologySnapshotsSnapshotIdGet(self, snapshot_id: str | int) -> Any:
        """Get Ontology Snapshot"""
        path = f"/v1/ontology/snapshots/{snapshot_id}"
        return self._request("GET", path)

    def ontologyLiabilityV1OntologyLiabilityPost(self, payload: Any) -> Any:
        """Ontology Liability"""
        path = f"/v1/ontology/liability"
        return self._request("POST", path, payload=payload)

    def inferV1InferPost(self, payload: Any) -> Any:
        """Infer"""
        path = f"/v1/infer"
        return self._request("POST", path, payload=payload)

    def enqueueVideoCleanV1JobsVideoCleanPost(self, payload: Any) -> Any:
        """Enqueue Video Clean"""
        path = f"/v1/jobs/video-clean"
        return self._request("POST", path, payload=payload)

    def enqueueBatchInferV1JobsBatchInferPost(self, payload: Any) -> Any:
        """Enqueue Batch Infer"""
        path = f"/v1/jobs/batch-infer"
        return self._request("POST", path, payload=payload)

    def listJobsV1JobsGet(self, query: dict[str, str | int | float | bool] | None = None) -> Any:
        """List Jobs"""
        path = f"/v1/jobs"
        if query:
            encoded = httpx.QueryParams(query)
            path = f"{path}?{encoded}"
        return self._request("GET", path)

    def getJobV1JobsJobIdGet(self, job_id: str | int) -> Any:
        """Get Job"""
        path = f"/v1/jobs/{job_id}"
        return self._request("GET", path)

    def retrievalUpsertV1RetrievalUpsertPost(self, payload: Any) -> Any:
        """Retrieval Upsert"""
        path = f"/v1/retrieval/upsert"
        return self._request("POST", path, payload=payload)

    def retrievalQueryV1RetrievalQueryPost(self, payload: Any) -> Any:
        """Retrieval Query"""
        path = f"/v1/retrieval/query"
        return self._request("POST", path, payload=payload)

    def videoPacketV1VideoPacketPost(self, payload: Any) -> Any:
        """Video Packet"""
        path = f"/v1/video/packet"
        return self._request("POST", path, payload=payload)

    def videoCleanV1VideoCleanPost(self, payload: Any) -> Any:
        """Video Clean"""
        path = f"/v1/video/clean"
        return self._request("POST", path, payload=payload)

    def smokeBenchmarkV1BenchmarksSmokeGet(self, query: dict[str, str | int | float | bool] | None = None) -> Any:
        """Smoke Benchmark"""
        path = f"/v1/benchmarks/smoke"
        if query:
            encoded = httpx.QueryParams(query)
            path = f"{path}?{encoded}"
        return self._request("GET", path)

    def metricsMetricsGet(self) -> Any:
        """Metrics"""
        path = f"/metrics"
        return self._request("GET", path)
