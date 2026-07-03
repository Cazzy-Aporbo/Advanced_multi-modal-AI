# Runtime Proof Bundle

- Service: `advanced-multimodal-ai`
- Version: `0.5.0`
- Environment: `development`
- Route count: `64`
- Test count: `36`
- Verification artifacts: `8`

## Connector kinds
- `local_csv`
- `local_jsonl`
- `local_parquet`
- `s3_parquet`
- `http_json`
- `http_ndjson`
- `web_html`

## Verification commands
- `python3 -m ruff check src tests scripts`
- `python3 -m pytest -q`
- `cargo test -p multimodal-core`
- `python3 scripts/export_openapi.py`
- `python3 scripts/generate_sdk_surfaces.py`
- `python3 scripts/export_research_surfaces.py`
- `python3 scripts/export_repository_pulse.py`
- `python3 scripts/export_execution_journal.py`
- `python3 scripts/run_acceptance_spine.py`
- `python3 scripts/export_readiness_report.py`
- `python3 scripts/export_example_bundle.py`
- `npm run --prefix sdk/typescript check`

## Verification artifacts
- `OpenAPI contract` · present · `openapi/openapi.json`
- `TypeScript generated client` · present · `sdk/typescript/src/generated-openapi.ts`
- `Python generated client` · present · `sdk/python/src/advanced_multimodal_ai_client/generated_openapi.py`
- `Runtime schema` · present · `sql/runtime_schema.sql`
- `Rust core` · present · `crates/multimodal-core/Cargo.toml`
- `Research surface export` · present · `proof/research-surfaces.json`
- `Repository pulse export` · present · `proof/repository-pulse.json`
- `Execution journal export` · present · `proof/execution-journal.json`
