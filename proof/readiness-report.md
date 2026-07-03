# Runtime Readiness Report

- Posture: `review_ready`
- Route count: `48`
- Test count: `32`
- Connector kinds: `local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html`
- Compiled recipes: `14`
- Fully resolved recipes: `14`

## Checks

- `pass` contract_surface: 48 public runtime surfaces are exported.
- `pass` verification_depth: 32 tests are currently counted in the proof bundle.
- `pass` artifact_evidence: 5 of 5 declared verification artifacts are present.
- `pass` connector_coverage: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html
- `pass` connector_evidence: 64 persisted connector runs are recorded.
- `pass` recipe_resolution: 14 of 14 compiled recipes have fully resolved source evidence.
- `pass` governance_evidence: drift baselines=8, ontology snapshots=53, pipeline runs=76

## Blockers

- none

## Boundaries

- **distributed execution**: Compiled recipes describe launch topology and checked manifest export, but an external trainer still executes the run.
- **cloud credentials**: The S3 Parquet lane depends on caller-managed credentials and does not store secrets inside the runtime.
- **public web intake**: The web_html lane is limited to public pages, domain allowlists, robots-aware fetch rules, and byte-capped extraction.
- **serving topology**: The repository proves a single-service runtime edge with supporting stores, not a hidden multi-cluster control plane.
