# Example Runtime Bundle

- Service: `advanced-multimodal-ai`
- Version: `0.5.0`
- Created at: `2026-07-06T00:49:19.260708+00:00`

## Inference

- Request id: `7da153c7-6397-40d1-9c15-317ed74e439e`
- Route: `validate_payloads, encode_audio, encode_text, fuse_modalities, emit_target`
- Output keys: `class_logits, class_probabilities, fused_embedding, modality_embeddings, predicted_index`

## Quality profile

- Fusion readiness: `0.9751953959465026`
- Modality count: `2`
- Warning count: `0`

## Connector ingest

- Connector kind: `local_parquet`
- Record count: `3`
- Pipeline status: `accepted`

## Public web intake

- Dataset id: `9b329620-5671-462d-919f-112968976aaa`
- Record count: `4`
- Title row: `Example Intake`
- Block kinds: `title, heading, paragraph, paragraph`

## Recipe manifest

- Recipe id: `a8fcf579-ce28-4e6a-a2e3-afd1182ae557`
- Launcher: `python`
- Engine: `local`
- Estimated global batch size: `4`

## Video cleanup

- Clip id: `example-clip-01`
- Removed spans: `1`
- Retained spans: `1`

## Benchmark

- Benchmark id: `9dfe8090-a013-4728-8b3f-b9cb383ba03f`
- Iterations: `3`
- Median latency ms: `14.72762500634417`
- P95 latency ms: `14.72762500634417`

## Proof

- Route count: `106`
- Test count: `64`
- Verification commands: `22`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html`

## Readiness

- Posture: `review_ready`
- Compiled recipes: `197`
- Resolved recipes: `197`
- Checks: `contract_surface, verification_depth, artifact_evidence, connector_coverage, connector_evidence, recipe_resolution, governance_evidence, stewardship_surface, execution_history`
