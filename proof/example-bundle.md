# Example Runtime Bundle

- Service: `advanced-multimodal-ai`
- Version: `0.5.0`
- Created at: `2026-07-03T18:47:30.046665+00:00`

## Inference

- Request id: `66c2fe9c-b964-4392-98bc-3f1ab75227a8`
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

- Dataset id: `b3d486c6-f055-4972-9ec8-7a1ee35f00db`
- Record count: `4`
- Title row: `Example Intake`
- Block kinds: `title, heading, paragraph, paragraph`

## Recipe manifest

- Recipe id: `a6a34fe0-dd3e-40d8-ac7f-c152b4352290`
- Launcher: `python`
- Engine: `local`
- Estimated global batch size: `4`

## Video cleanup

- Clip id: `example-clip-01`
- Removed spans: `1`
- Retained spans: `1`

## Benchmark

- Benchmark id: `6eef860a-cd29-44b0-99f1-20a7a18b52a1`
- Iterations: `3`
- Median latency ms: `14.539625000907108`
- P95 latency ms: `14.539625000907108`

## Proof

- Route count: `69`
- Test count: `46`
- Verification commands: `15`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html`

## Readiness

- Posture: `review_ready`
- Compiled recipes: `79`
- Resolved recipes: `79`
- Checks: `contract_surface, verification_depth, artifact_evidence, connector_coverage, connector_evidence, recipe_resolution, governance_evidence, stewardship_surface, execution_history`
