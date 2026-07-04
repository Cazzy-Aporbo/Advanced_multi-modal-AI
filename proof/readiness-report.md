# Runtime Readiness Report

- Posture: `review_ready`
- Route count: `95`
- Test count: `55`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html`
- Compiled recipes: `159`
- Fully resolved recipes: `159`

## Checks

- `pass` contract_surface: 95 public runtime surfaces are exported.
- `pass` verification_depth: 55 tests are currently counted in the proof bundle.
- `pass` artifact_evidence: 16 of 16 declared verification artifacts are present.
- `pass` connector_coverage: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html
- `pass` connector_evidence: 497 persisted connector runs are recorded.
- `pass` recipe_resolution: 159 of 159 compiled recipes have fully resolved source evidence.
- `pass` governance_evidence: drift baselines=8, ontology snapshots=130, pipeline runs=382
- `pass` stewardship_surface: lifecycle policies=33, change controls=33, supply snapshots=33
- `pass` execution_history: 188 persisted export or verification runs are recorded.

## Blockers

- none

## Boundaries

- **distributed execution**: Compiled recipes describe launch topology and checked manifest export, but an external trainer still executes the run.
- **cloud credentials**: The S3 Parquet lane depends on caller-managed credentials and does not store secrets inside the runtime.
- **public web intake**: The web_html lane is limited to public pages, domain allowlists, robots-aware fetch rules, and byte-capped extraction.
- **serving topology**: The repository proves a single-service runtime edge with supporting stores, not a hidden multi-cluster control plane.
- **data retirement**: Lifecycle, change-control, and supply-chain surfaces document review, retention, and removal intent, but external schedulers still carry out the physical delete or archive operation.
