# Example Runtime Bundle

- Service: `advanced-multimodal-ai`
- Version: `0.4.0`
- Created at: `2026-07-03T06:16:19.365022+00:00`

## Inference

- Request id: `e8fc3013-d2ca-436d-bf97-b0366a8ef5b8`
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

## Recipe manifest

- Recipe id: `32a80a72-642e-4e4b-b060-00a7e9cd8ad4`
- Launcher: `python`
- Engine: `local`
- Estimated global batch size: `4`

## Video cleanup

- Clip id: `example-clip-01`
- Removed spans: `1`
- Retained spans: `1`

## Benchmark

- Benchmark id: `1168643d-9344-493f-96a6-b649ede0619b`
- Iterations: `3`
- Median latency ms: `13.754333998804213`
- P95 latency ms: `13.754333998804213`

## Proof

- Route count: `48`
- Test count: `29`
- Verification commands: `9`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson`

## Readiness

- Posture: `review_ready`
- Compiled recipes: `12`
- Resolved recipes: `12`
- Checks: `contract_surface, verification_depth, artifact_evidence, connector_coverage, connector_evidence, recipe_resolution, governance_evidence`
