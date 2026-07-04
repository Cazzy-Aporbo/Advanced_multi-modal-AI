# Example Runtime Bundle

- Service: `advanced-multimodal-ai`
- Version: `0.5.0`
- Created at: `2026-07-04T03:01:48.664750+00:00`

## Inference

- Request id: `435cf02d-f61c-47fd-9c03-81a64426a152`
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

- Dataset id: `74cdf7bd-e3a0-4da0-89ed-054fe4d91063`
- Record count: `4`
- Title row: `Example Intake`
- Block kinds: `title, heading, paragraph, paragraph`

## Recipe manifest

- Recipe id: `55d35e4e-3531-4f97-9b73-9c96e6decf29`
- Launcher: `python`
- Engine: `local`
- Estimated global batch size: `4`

## Video cleanup

- Clip id: `example-clip-01`
- Removed spans: `1`
- Retained spans: `1`

## Benchmark

- Benchmark id: `6f4aead7-6760-41e4-bdf2-622e76d60754`
- Iterations: `3`
- Median latency ms: `13.662208002642728`
- P95 latency ms: `13.662208002642728`

## Proof

- Route count: `95`
- Test count: `55`
- Verification commands: `21`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html`

## Readiness

- Posture: `review_ready`
- Compiled recipes: `160`
- Resolved recipes: `160`
- Checks: `contract_surface, verification_depth, artifact_evidence, connector_coverage, connector_evidence, recipe_resolution, governance_evidence, stewardship_surface, execution_history`
