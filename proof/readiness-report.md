# Runtime Readiness Report

- Posture: `needs_buildout`
- Route count: `63`
- Test count: `35`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html`
- Compiled recipes: `29`
- Fully resolved recipes: `29`

## Checks

- `pass` contract_surface: 63 public runtime surfaces are exported.
- `pass` verification_depth: 35 tests are currently counted in the proof bundle.
- `fail` artifact_evidence: 6 of 7 declared verification artifacts are present.
- `pass` connector_coverage: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html
- `pass` connector_evidence: 150 persisted connector runs are recorded.
- `pass` recipe_resolution: 29 of 29 compiled recipes have fully resolved source evidence.
- `pass` governance_evidence: drift baselines=8, ontology snapshots=72, pipeline runs=131
- `pass` stewardship_surface: lifecycle policies=8, change controls=8, supply snapshots=8

## Blockers

- 6 of 7 declared verification artifacts are present.

## Boundaries

- **distributed execution**: Compiled recipes describe launch topology and checked manifest export, but an external trainer still executes the run.
- **cloud credentials**: The S3 Parquet lane depends on caller-managed credentials and does not store secrets inside the runtime.
- **public web intake**: The web_html lane is limited to public pages, domain allowlists, robots-aware fetch rules, and byte-capped extraction.
- **serving topology**: The repository proves a single-service runtime edge with supporting stores, not a hidden multi-cluster control plane.
- **data retirement**: Lifecycle, change-control, and supply-chain surfaces document review, retention, and removal intent, but external schedulers still carry out the physical delete or archive operation.
