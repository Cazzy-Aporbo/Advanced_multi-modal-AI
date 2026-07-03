# Example Runtime Bundle

- Service: `advanced-multimodal-ai`
- Version: `0.4.0`
- Created at: `2026-07-03T06:46:39.227562+00:00`

## Inference

- Request id: `43350ce6-7858-4c9d-927a-b259552e1192`
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

- Dataset id: `118ecca7-774c-49c6-b873-d5aa4f65783b`
- Record count: `4`
- Title row: `Example Intake`
- Block kinds: `title, heading, paragraph, paragraph`

## Recipe manifest

- Recipe id: `150f8f0b-d145-48a3-b97f-6c392fd66f88`
- Launcher: `python`
- Engine: `local`
- Estimated global batch size: `4`

## Video cleanup

- Clip id: `example-clip-01`
- Removed spans: `1`
- Retained spans: `1`

## Benchmark

- Benchmark id: `a0b2a85d-bc72-4608-8935-baab1b96eb13`
- Iterations: `3`
- Median latency ms: `15.471917000468238`
- P95 latency ms: `15.471917000468238`

## Proof

- Route count: `48`
- Test count: `32`
- Verification commands: `9`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html`

## Readiness

- Posture: `review_ready`
- Compiled recipes: `16`
- Resolved recipes: `16`
- Checks: `contract_surface, verification_depth, artifact_evidence, connector_coverage, connector_evidence, recipe_resolution, governance_evidence`
