# Example Runtime Bundle

- Service: `advanced-multimodal-ai`
- Version: `0.5.0`
- Created at: `2026-07-03T08:12:18.972037+00:00`

## Inference

- Request id: `5d5d376a-2cac-4761-bf31-76f382068136`
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

- Dataset id: `e5b2e3ad-32ed-479f-b210-daf4ebf547b9`
- Record count: `4`
- Title row: `Example Intake`
- Block kinds: `title, heading, paragraph, paragraph`

## Recipe manifest

- Recipe id: `8d754d20-9100-4471-8bb5-350749edd59b`
- Launcher: `python`
- Engine: `local`
- Estimated global batch size: `4`

## Video cleanup

- Clip id: `example-clip-01`
- Removed spans: `1`
- Retained spans: `1`

## Benchmark

- Benchmark id: `e239255f-09cf-4a18-96b2-59611d0a6c65`
- Iterations: `3`
- Median latency ms: `15.758665998873767`
- P95 latency ms: `15.758665998873767`

## Proof

- Route count: `64`
- Test count: `36`
- Verification commands: `12`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html`

## Readiness

- Posture: `needs_buildout`
- Compiled recipes: `33`
- Resolved recipes: `33`
- Checks: `contract_surface, verification_depth, artifact_evidence, connector_coverage, connector_evidence, recipe_resolution, governance_evidence, stewardship_surface, execution_history`
