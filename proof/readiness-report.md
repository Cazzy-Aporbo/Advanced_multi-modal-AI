# Runtime Readiness Report

- Posture: `review_ready`
- Route count: `106`
- Test count: `64`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html`
- Compiled recipes: `196`
- Fully resolved recipes: `196`

## Checks

- `pass` contract_surface: 106 public runtime surfaces are exported.
- `pass` verification_depth: 64 tests are currently counted in the proof bundle.
- `pass` artifact_evidence: 18 of 18 declared verification artifacts are present.
- `pass` connector_coverage: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html
- `pass` connector_evidence: 541 persisted connector runs are recorded.
- `pass` recipe_resolution: 196 of 196 compiled recipes have fully resolved source evidence.
- `pass` governance_evidence: drift baselines=8, ontology snapshots=131, pipeline runs=422
- `pass` stewardship_surface: lifecycle policies=33, change controls=33, supply snapshots=33
- `pass` execution_history: 309 persisted export or verification runs are recorded.

## Blockers

- none

## Boundaries

- **distributed execution**: Compiled recipes describe launch topology and checked manifest export, but an external trainer still executes the run.
- **cloud credentials**: The S3 Parquet lane depends on caller-managed credentials and does not store secrets inside the runtime.
- **public web intake**: The web_html lane is limited to public pages, domain allowlists, robots-aware fetch rules, and byte-capped extraction.
- **serving topology**: The repository proves a single-service runtime edge with supporting stores, not a hidden multi-cluster control plane.
- **data retirement**: Lifecycle, change-control, and supply-chain surfaces document review, retention, and removal intent, but external schedulers still carry out the physical delete or archive operation.
