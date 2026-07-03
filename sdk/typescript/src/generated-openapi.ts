// Generated from openapi/openapi.json. Do not edit by hand.

export class GeneratedOpenAPIClient {
  constructor(private readonly baseUrl: string) {}

  private async request<T>(method: string, path: string, payload?: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: payload === undefined ? undefined : { "content-type": "application/json" },
      body: payload === undefined ? undefined : JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }
    return response.json() as Promise<T>;
  }

  /** Root */
  async rootGet(): Promise<unknown> {
    let path = `/`;
    return this.request<unknown>("GET", path);
  }

  /** Health */
  async healthV1HealthGet(): Promise<unknown> {
    let path = `/v1/health`;
    return this.request<unknown>("GET", path);
  }

  /** Ready */
  async readyV1ReadyGet(): Promise<unknown> {
    let path = `/v1/ready`;
    return this.request<unknown>("GET", path);
  }

  /** Models */
  async modelsV1ModelsGet(): Promise<unknown> {
    let path = `/v1/models`;
    return this.request<unknown>("GET", path);
  }

  /** Research Models */
  async researchModelsV1ResearchModelsGet(): Promise<unknown> {
    let path = `/v1/research/models`;
    return this.request<unknown>("GET", path);
  }

  /** Research Findings */
  async researchFindingsV1ResearchFindingsGet(): Promise<unknown> {
    let path = `/v1/research/findings`;
    return this.request<unknown>("GET", path);
  }

  /** Research Connections */
  async researchConnectionsV1ResearchConnectionsGet(): Promise<unknown> {
    let path = `/v1/research/connections`;
    return this.request<unknown>("GET", path);
  }

  /** Research Surfaces */
  async researchSurfacesV1ResearchSurfacesGet(): Promise<unknown> {
    let path = `/v1/research/surfaces`;
    return this.request<unknown>("GET", path);
  }

  /** Research Cymatic Surface */
  async researchCymaticSurfaceV1ResearchCymaticSurfaceGet(): Promise<unknown> {
    let path = `/v1/research/cymatic-surface`;
    return this.request<unknown>("GET", path);
  }

  /** Repository Pulse */
  async repositoryPulseV1RepositoryPulseGet(): Promise<unknown> {
    let path = `/v1/repository/pulse`;
    return this.request<unknown>("GET", path);
  }

  /** Execution Journal */
  async executionJournalV1ExecutionJournalGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/execution/journal`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Register Dataset */
  async registerDatasetV1CatalogRegisterPost(payload: unknown): Promise<unknown> {
    let path = `/v1/catalog/register`;
    return this.request<unknown>("POST", path, payload);
  }

  /** List Datasets */
  async listDatasetsV1CatalogDatasetsGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/catalog/datasets`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Get Dataset */
  async getDatasetV1CatalogDatasetsDatasetIdGet(dataset_id: string | number): Promise<unknown> {
    let path = `/v1/catalog/datasets/${encodeURIComponent(String(dataset_id))}`;
    return this.request<unknown>("GET", path);
  }

  /** Compare Dataset Evolution */
  async compareDatasetEvolutionV1CatalogEvolutionPost(payload: unknown): Promise<unknown> {
    let path = `/v1/catalog/evolution`;
    return this.request<unknown>("POST", path, payload);
  }

  /** List Lifecycle Policies */
  async listLifecyclePoliciesV1StewardshipLifecycleGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/stewardship/lifecycle`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Register Lifecycle Policy */
  async registerLifecyclePolicyV1StewardshipLifecyclePost(payload: unknown): Promise<unknown> {
    let path = `/v1/stewardship/lifecycle`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Get Lifecycle Policy */
  async getLifecyclePolicyV1StewardshipLifecyclePolicyIdGet(policy_id: string | number): Promise<unknown> {
    let path = `/v1/stewardship/lifecycle/${encodeURIComponent(String(policy_id))}`;
    return this.request<unknown>("GET", path);
  }

  /** List Change Controls */
  async listChangeControlsV1StewardshipChangeControlsGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/stewardship/change-controls`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Create Change Control */
  async createChangeControlV1StewardshipChangeControlsPost(payload: unknown): Promise<unknown> {
    let path = `/v1/stewardship/change-controls`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Get Change Control */
  async getChangeControlV1StewardshipChangeControlsChangeIdGet(change_id: string | number): Promise<unknown> {
    let path = `/v1/stewardship/change-controls/${encodeURIComponent(String(change_id))}`;
    return this.request<unknown>("GET", path);
  }

  /** List Supply Chain Snapshots */
  async listSupplyChainSnapshotsV1StewardshipSupplyChainGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/stewardship/supply-chain`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Create Supply Chain Snapshot */
  async createSupplyChainSnapshotV1StewardshipSupplyChainPost(payload: unknown): Promise<unknown> {
    let path = `/v1/stewardship/supply-chain`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Get Supply Chain Snapshot */
  async getSupplyChainSnapshotV1StewardshipSupplyChainSnapshotIdGet(snapshot_id: string | number): Promise<unknown> {
    let path = `/v1/stewardship/supply-chain/${encodeURIComponent(String(snapshot_id))}`;
    return this.request<unknown>("GET", path);
  }

  /** Stewardship Posture */
  async stewardshipPostureV1StewardshipPostureGet(): Promise<unknown> {
    let path = `/v1/stewardship/posture`;
    return this.request<unknown>("GET", path);
  }

  /** Register Connector Dataset */
  async registerConnectorDatasetV1ConnectorsRegisterPost(payload: unknown): Promise<unknown> {
    let path = `/v1/connectors/register`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Connector Pipeline Ingest */
  async connectorPipelineIngestV1ConnectorsPipelineIngestPost(payload: unknown): Promise<unknown> {
    let path = `/v1/connectors/pipeline-ingest`;
    return this.request<unknown>("POST", path, payload);
  }

  /** List Connector Runs */
  async listConnectorRunsV1ConnectorsRunsGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/connectors/runs`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Get Connector Run */
  async getConnectorRunV1ConnectorsRunsRunIdGet(run_id: string | number): Promise<unknown> {
    let path = `/v1/connectors/runs/${encodeURIComponent(String(run_id))}`;
    return this.request<unknown>("GET", path);
  }

  /** Runtime Attestation */
  async runtimeAttestationV1RuntimeAttestationGet(): Promise<unknown> {
    let path = `/v1/runtime/attestation`;
    return this.request<unknown>("GET", path);
  }

  /** Runtime Compliance Ledger */
  async runtimeComplianceLedgerV1RuntimeComplianceLedgerGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/runtime/compliance-ledger`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Runtime Proof Bundle */
  async runtimeProofBundleV1ProofBundleGet(): Promise<unknown> {
    let path = `/v1/proof/bundle`;
    return this.request<unknown>("GET", path);
  }

  /** Readiness Report */
  async readinessReportV1ReadinessReportGet(): Promise<unknown> {
    let path = `/v1/readiness/report`;
    return this.request<unknown>("GET", path);
  }

  /** Bias Taxonomy */
  async biasTaxonomyV1BiasTaxonomyGet(): Promise<unknown> {
    let path = `/v1/bias/taxonomy`;
    return this.request<unknown>("GET", path);
  }

  /** Bias Assessment */
  async biasAssessmentV1BiasAssessPost(payload: unknown): Promise<unknown> {
    let path = `/v1/bias/assess`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Plan */
  async planV1PlanPost(payload: unknown): Promise<unknown> {
    let path = `/v1/plan`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Compile Recipe */
  async compileRecipeV1RecipesCompilePost(payload: unknown): Promise<unknown> {
    let path = `/v1/recipes/compile`;
    return this.request<unknown>("POST", path, payload);
  }

  /** List Recipes */
  async listRecipesV1RecipesGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/recipes`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Get Recipe */
  async getRecipeV1RecipesRecipeIdGet(recipe_id: string | number): Promise<unknown> {
    let path = `/v1/recipes/${encodeURIComponent(String(recipe_id))}`;
    return this.request<unknown>("GET", path);
  }

  /** Data Profile */
  async dataProfileV1DataProfilePost(payload: unknown): Promise<unknown> {
    let path = `/v1/data/profile`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Data Intercept */
  async dataInterceptV1DataInterceptPost(payload: unknown): Promise<unknown> {
    let path = `/v1/data/intercept`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Data Provenance */
  async dataProvenanceV1DataProvenancePost(payload: unknown): Promise<unknown> {
    let path = `/v1/data/provenance`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Alignment Windows */
  async alignmentWindowsV1AlignmentWindowsPost(payload: unknown): Promise<unknown> {
    let path = `/v1/alignment/windows`;
    return this.request<unknown>("POST", path, payload);
  }

  /** List Drift Baselines */
  async listDriftBaselinesV1DriftBaselinesGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/drift/baselines`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Create Drift Baseline */
  async createDriftBaselineV1DriftBaselinesPost(payload: unknown): Promise<unknown> {
    let path = `/v1/drift/baselines`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Population Drift Check */
  async populationDriftCheckV1DriftCheckPost(payload: unknown): Promise<unknown> {
    let path = `/v1/drift/check`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Pipeline Ingest */
  async pipelineIngestV1PipelinesIngestPost(payload: unknown): Promise<unknown> {
    let path = `/v1/pipelines/ingest`;
    return this.request<unknown>("POST", path, payload);
  }

  /** List Pipeline Runs */
  async listPipelineRunsV1PipelinesRunsGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/pipelines/runs`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Get Pipeline Run */
  async getPipelineRunV1PipelinesRunsRunIdGet(run_id: string | number): Promise<unknown> {
    let path = `/v1/pipelines/runs/${encodeURIComponent(String(run_id))}`;
    return this.request<unknown>("GET", path);
  }

  /** Export Pipeline Run */
  async exportPipelineRunV1PipelinesRunsRunIdExportGet(run_id: string | number): Promise<unknown> {
    let path = `/v1/pipelines/runs/${encodeURIComponent(String(run_id))}/export`;
    return this.request<unknown>("GET", path);
  }

  /** Replay Pipeline Run */
  async replayPipelineRunV1PipelinesRunsRunIdReplayPost(run_id: string | number): Promise<unknown> {
    let path = `/v1/pipelines/runs/${encodeURIComponent(String(run_id))}/replay`;
    return this.request<unknown>("POST", path);
  }

  /** Ontology Ingest */
  async ontologyIngestV1OntologyIngestPost(payload: unknown): Promise<unknown> {
    let path = `/v1/ontology/ingest`;
    return this.request<unknown>("POST", path, payload);
  }

  /** List Ontology Snapshots */
  async listOntologySnapshotsV1OntologySnapshotsGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/ontology/snapshots`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Get Ontology Snapshot */
  async getOntologySnapshotV1OntologySnapshotsSnapshotIdGet(snapshot_id: string | number): Promise<unknown> {
    let path = `/v1/ontology/snapshots/${encodeURIComponent(String(snapshot_id))}`;
    return this.request<unknown>("GET", path);
  }

  /** Ontology Liability */
  async ontologyLiabilityV1OntologyLiabilityPost(payload: unknown): Promise<unknown> {
    let path = `/v1/ontology/liability`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Infer */
  async inferV1InferPost(payload: unknown): Promise<unknown> {
    let path = `/v1/infer`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Enqueue Video Clean */
  async enqueueVideoCleanV1JobsVideoCleanPost(payload: unknown): Promise<unknown> {
    let path = `/v1/jobs/video-clean`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Enqueue Batch Infer */
  async enqueueBatchInferV1JobsBatchInferPost(payload: unknown): Promise<unknown> {
    let path = `/v1/jobs/batch-infer`;
    return this.request<unknown>("POST", path, payload);
  }

  /** List Jobs */
  async listJobsV1JobsGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/jobs`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Get Job */
  async getJobV1JobsJobIdGet(job_id: string | number): Promise<unknown> {
    let path = `/v1/jobs/${encodeURIComponent(String(job_id))}`;
    return this.request<unknown>("GET", path);
  }

  /** Retrieval Upsert */
  async retrievalUpsertV1RetrievalUpsertPost(payload: unknown): Promise<unknown> {
    let path = `/v1/retrieval/upsert`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Retrieval Query */
  async retrievalQueryV1RetrievalQueryPost(payload: unknown): Promise<unknown> {
    let path = `/v1/retrieval/query`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Video Packet */
  async videoPacketV1VideoPacketPost(payload: unknown): Promise<unknown> {
    let path = `/v1/video/packet`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Video Clean */
  async videoCleanV1VideoCleanPost(payload: unknown): Promise<unknown> {
    let path = `/v1/video/clean`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Smoke Benchmark */
  async smokeBenchmarkV1BenchmarksSmokeGet(query: Record<string, string | number | boolean | undefined> = {}): Promise<unknown> {
    let path = `/v1/benchmarks/smoke`;
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        search.set(key, String(value));
      }
    }
    const queryString = search.toString();
    if (queryString) {
      path += `?${queryString}`;
    }
    return this.request<unknown>("GET", path);
  }

  /** Reference Benchmark Default */
  async referenceBenchmarkDefaultV1BenchmarksReferenceGet(): Promise<unknown> {
    let path = `/v1/benchmarks/reference`;
    return this.request<unknown>("GET", path);
  }

  /** Reference Benchmark */
  async referenceBenchmarkV1BenchmarksReferencePost(payload: unknown): Promise<unknown> {
    let path = `/v1/benchmarks/reference`;
    return this.request<unknown>("POST", path, payload);
  }

  /** Metrics */
  async metricsMetricsGet(): Promise<unknown> {
    let path = `/metrics`;
    return this.request<unknown>("GET", path);
  }

}
