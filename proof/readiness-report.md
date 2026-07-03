# Runtime Readiness Report

- Posture: `review_ready`
- Route count: `48`
- Test count: `29`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson`
- Compiled recipes: `11`
- Fully resolved recipes: `11`

## Checks

- `pass` contract_surface: 48 public runtime surfaces are exported.
- `pass` verification_depth: 29 tests are currently counted in the proof bundle.
- `pass` artifact_evidence: 5 of 5 declared verification artifacts are present.
- `pass` connector_coverage: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson
- `pass` connector_evidence: 38 persisted connector runs are recorded.
- `pass` recipe_resolution: 11 of 11 compiled recipes have fully resolved source evidence.
- `pass` governance_evidence: drift baselines=8, ontology snapshots=46, pipeline runs=57

## Blockers

- none

## Boundaries

- **distributed execution**: Compiled recipes describe launch topology and checked manifest export, but an external trainer still executes the run.
- **cloud credentials**: The S3 Parquet lane depends on caller-managed credentials and does not store secrets inside the runtime.
- **serving topology**: The repository proves a single-service runtime edge with supporting stores, not a hidden multi-cluster control plane.
