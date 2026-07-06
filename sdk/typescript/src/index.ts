export type ModalityKind = "text" | "image" | "audio" | "video" | "sensor" | "tabular";
export type RuntimeMode = "contract" | "research";
export type TargetKind = "embedding" | "classification" | "retrieval" | "translation";

export interface TensorPayload {
  shape: number[];
  values: number[];
  dtype?: string;
}

export interface InferenceRequest {
  model_id?: string;
  runtime_mode?: RuntimeMode;
  target?: TargetKind;
  num_classes?: number | null;
  return_embeddings?: boolean;
  return_uncertainty?: boolean;
  modalities: Partial<Record<ModalityKind, TensorPayload>>;
  metadata?: Record<string, unknown>;
}

export interface HealthResponse {
  service: string;
  version: string;
  environment: string;
  status: "ok" | "degraded";
  torch_available: boolean;
  metrics_enabled: boolean;
  created_at: string;
}

export interface ModalityQualityProfile {
  modality: ModalityKind;
  batch_size: number;
  feature_width: number;
  value_count: number;
  finite_ratio: number;
  zero_ratio: number;
  entropy_score: number;
  energy_score: number;
  dynamic_range: number;
  temporal_change: number;
  status: "ok" | "watch" | "fail";
  notes: string[];
}

export interface PairwiseAlignmentProfile {
  left_modality: ModalityKind;
  right_modality: ModalityKind;
  cosine_alignment: number;
  mean_gap: number;
  note: string;
}

export interface DataProfileResponse {
  request_id: string;
  model_id: string;
  runtime_mode: RuntimeMode;
  modality_profiles: ModalityQualityProfile[];
  pairwise_alignment: PairwiseAlignmentProfile[];
  coverage_score: number;
  fusion_readiness: number;
  warnings: string[];
  created_at: string;
}

export interface ProvenanceReceipt {
  receipt_id: string;
  request_id: string;
  model_id: string;
  runtime_mode: RuntimeMode;
  modality_digests: Partial<Record<ModalityKind, string>>;
  metadata_digest: string;
  payload_digest: string;
  notes: string[];
  created_at: string;
}

export interface RegisteredModelResponse {
  model_id: string;
  label: string;
  runtime_ready: boolean;
  supports_contract_mode: boolean;
  supports_research_mode: boolean;
  source_file: string;
  notes: string;
}

export interface StreamEvent {
  event: string;
  [key: string]: unknown;
}

export interface TensorValidationIssue {
  modality: ModalityKind;
  code:
    | "missing-shape"
    | "missing-values"
    | "invalid-dimension"
    | "length-mismatch"
    | "non-finite-value";
  message: string;
}

export interface TensorValidationReport {
  ok: boolean;
  issueCount: number;
  totalValues: number;
  modalities: ModalityKind[];
  issues: TensorValidationIssue[];
}

export interface TemporalObservation {
  modality: ModalityKind;
  start_ms: number;
  end_ms: number;
  confidence?: number;
  source_id?: string;
  note?: string;
  attributes?: Record<string, unknown>;
}

export interface TemporalAlignmentRequest {
  observations: TemporalObservation[];
  merge_gap_ms?: number;
  minimum_modalities?: number;
  include_singletons?: boolean;
}

export interface TemporalAlignmentWindow {
  span: { start_ms: number; end_ms: number };
  modalities: ModalityKind[];
  observation_count: number;
  average_confidence: number;
  source_ids: string[];
  note: string;
}

export interface TemporalAlignmentResponse {
  windows: TemporalAlignmentWindow[];
  modality_coverage_ms: Partial<Record<ModalityKind, number>>;
  uncovered_modalities: ModalityKind[];
  created_at: string;
}

export { GeneratedOpenAPIClient } from "./generated-openapi.js";

export class AdvancedMultimodalAIClient {
  private readonly baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  async health(): Promise<HealthResponse> {
    return this.get<HealthResponse>("/v1/health");
  }

  async models(): Promise<RegisteredModelResponse[]> {
    return this.get<RegisteredModelResponse[]>("/v1/models");
  }

  async profile(payload: InferenceRequest): Promise<DataProfileResponse> {
    assertInferenceRequest(payload);
    return this.post<DataProfileResponse>("/v1/data/profile", payload);
  }

  async provenance(payload: InferenceRequest): Promise<ProvenanceReceipt> {
    assertInferenceRequest(payload);
    return this.post<ProvenanceReceipt>("/v1/data/provenance", payload);
  }

  async alignWindows(
    payload: TemporalAlignmentRequest,
  ): Promise<TemporalAlignmentResponse> {
    return this.post<TemporalAlignmentResponse>("/v1/alignment/windows", payload);
  }

  async infer(payload: InferenceRequest): Promise<unknown> {
    assertInferenceRequest(payload);
    return this.post("/v1/infer", payload);
  }

  async plan(payload: InferenceRequest): Promise<unknown> {
    assertInferenceRequest(payload);
    return this.post("/v1/plan", payload);
  }

  streamInference(
    payload: InferenceRequest,
    onEvent: (event: StreamEvent) => void,
  ): WebSocket {
    assertInferenceRequest(payload);
    const url = new URL(this.baseUrl);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = "/v1/stream";

    const socket = new WebSocket(url.toString());
    socket.addEventListener("open", () => {
      socket.send(JSON.stringify(payload));
    });
    socket.addEventListener("message", (message) => {
      onEvent(JSON.parse(String(message.data)) as StreamEvent);
    });
    return socket;
  }

  private async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`);
    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }
    return response.json() as Promise<T>;
  }

  private async post<T>(path: string, payload: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }
    return response.json() as Promise<T>;
  }
}

export function validateInferenceRequest(
  payload: InferenceRequest,
): TensorValidationReport {
  const issues: TensorValidationIssue[] = [];
  let totalValues = 0;
  const modalityMap = payload.modalities ?? {};
  const modalities = Object.keys(modalityMap) as ModalityKind[];

  for (const modality of modalities) {
    const tensor = modalityMap[modality];
    if (!tensor) continue;
    const values = Array.isArray(tensor.values) ? tensor.values : [];
    totalValues += values.length;
    if (!Array.isArray(tensor.values)) {
      issues.push({
        modality,
        code: "missing-values",
        message: "Tensor values must be supplied as a flat numeric array.",
      });
    }
    if (!Array.isArray(tensor.shape) || tensor.shape.length < 2) {
      issues.push({
        modality,
        code: "missing-shape",
        message: "Tensor shape must include at least batch and feature dimensions.",
      });
      continue;
    }
    const expected = tensor.shape.reduce((product, dimension) => {
      if (!Number.isInteger(dimension) || dimension <= 0) {
        issues.push({
          modality,
          code: "invalid-dimension",
          message: `Invalid tensor dimension: ${dimension}.`,
        });
      }
      return product * Math.max(0, dimension);
    }, 1);
    if (expected !== values.length) {
      issues.push({
        modality,
        code: "length-mismatch",
        message: `Shape ${tensor.shape.join("x")} expects ${expected} values, received ${values.length}.`,
      });
    }
    const firstBadIndex = values.findIndex((value) => !Number.isFinite(value));
    if (firstBadIndex >= 0) {
      issues.push({
        modality,
        code: "non-finite-value",
        message: `Non-finite tensor value at flattened index ${firstBadIndex}.`,
      });
    }
  }

  return {
    ok: issues.length === 0 && modalities.length > 0,
    issueCount: issues.length,
    totalValues,
    modalities,
    issues,
  };
}

export function assertInferenceRequest(payload: InferenceRequest): void {
  const report = validateInferenceRequest(payload);
  if (report.ok) return;
  const details =
    report.issues[0]?.message ?? "At least one modality payload is required.";
  throw new Error(`Invalid multimodal request: ${details}`);
}
