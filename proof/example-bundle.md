# Example Runtime Bundle

- Service: `advanced-multimodal-ai`
- Version: `0.5.0`
- Created at: `2026-07-04T04:03:25.312000+00:00`

## Inference

- Request id: `375b7d09-ecdf-43fc-9013-0f520f2d8b20`
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

- Dataset id: `82652b9f-eb17-45e5-be00-37c0c45ab928`
- Record count: `4`
- Title row: `Example Intake`
- Block kinds: `title, heading, paragraph, paragraph`

## Recipe manifest

- Recipe id: `c9c08739-de5d-4641-97d3-d8fdd9057526`
- Launcher: `python`
- Engine: `local`
- Estimated global batch size: `4`

## Video cleanup

- Clip id: `example-clip-01`
- Removed spans: `1`
- Retained spans: `1`

## Benchmark

- Benchmark id: `612fd5bc-3bc1-4953-b771-ef9b3ba27ddb`
- Iterations: `3`
- Median latency ms: `14.208374996087514`
- P95 latency ms: `14.208374996087514`

## Proof

- Route count: `100`
- Test count: `60`
- Verification commands: `21`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html`

## Readiness

- Posture: `review_ready`
- Compiled recipes: `165`
- Resolved recipes: `165`
- Checks: `contract_surface, verification_depth, artifact_evidence, connector_coverage, connector_evidence, recipe_resolution, governance_evidence, stewardship_surface, execution_history`
