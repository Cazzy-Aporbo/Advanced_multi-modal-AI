# Example Runtime Bundle

- Service: `advanced-multimodal-ai`
- Version: `0.5.0`
- Created at: `2026-07-03T20:14:02.887850+00:00`

## Inference

- Request id: `c71352b9-65cc-40a3-bb9c-c39368c11f26`
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

- Dataset id: `5d0212f2-dc9a-41b2-8d37-0ea796afe170`
- Record count: `4`
- Title row: `Example Intake`
- Block kinds: `title, heading, paragraph, paragraph`

## Recipe manifest

- Recipe id: `9268995b-d9c6-445f-94dd-01a11bf2f4ab`
- Launcher: `python`
- Engine: `local`
- Estimated global batch size: `4`

## Video cleanup

- Clip id: `example-clip-01`
- Removed spans: `1`
- Retained spans: `1`

## Benchmark

- Benchmark id: `2803b955-7592-4608-9175-6c2e3aeb8b05`
- Iterations: `3`
- Median latency ms: `15.174916996329557`
- P95 latency ms: `15.174916996329557`

## Proof

- Route count: `82`
- Test count: `48`
- Verification commands: `16`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html`

## Readiness

- Posture: `review_ready`
- Compiled recipes: `103`
- Resolved recipes: `103`
- Checks: `contract_surface, verification_depth, artifact_evidence, connector_coverage, connector_evidence, recipe_resolution, governance_evidence, stewardship_surface, execution_history`
