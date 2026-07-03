# Runtime Readiness Report

- Posture: `review_ready`
- Route count: `64`
- Test count: `36`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html`
- Compiled recipes: `33`
- Fully resolved recipes: `33`

## Checks

- `pass` contract_surface: 64 public runtime surfaces are exported.
- `pass` verification_depth: 36 tests are currently counted in the proof bundle.
- `pass` artifact_evidence: 8 of 8 declared verification artifacts are present.
- `pass` connector_coverage: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html
- `pass` connector_evidence: 169 persisted connector runs are recorded.
- `pass` recipe_resolution: 33 of 33 compiled recipes have fully resolved source evidence.
- `pass` governance_evidence: drift baselines=8, ontology snapshots=76, pipeline runs=142
- `pass` stewardship_surface: lifecycle policies=10, change controls=10, supply snapshots=10
- `pass` execution_history: 12 persisted export or verification runs are recorded.

## Blockers

- none

## Boundaries

- **distributed execution**: Compiled recipes describe launch topology and checked manifest export, but an external trainer still executes the run.
- **cloud credentials**: The S3 Parquet lane depends on caller-managed credentials and does not store secrets inside the runtime.
- **public web intake**: The web_html lane is limited to public pages, domain allowlists, robots-aware fetch rules, and byte-capped extraction.
- **serving topology**: The repository proves a single-service runtime edge with supporting stores, not a hidden multi-cluster control plane.
- **data retirement**: Lifecycle, change-control, and supply-chain surfaces document review, retention, and removal intent, but external schedulers still carry out the physical delete or archive operation.
