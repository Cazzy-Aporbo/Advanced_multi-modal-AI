# Runtime Proof Bundle

- Service: `advanced-multimodal-ai`
- Version: `0.5.0`
- Environment: `development`
- Route count: `105`
- Test count: `63`
- Verification artifacts: `17`

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
- `python3 -m pytest -q tests/test_property_fuzz.py`
- `cargo test -p multimodal-core`
- `python3 scripts/export_openapi.py`
- `python3 scripts/generate_sdk_surfaces.py`
- `python3 scripts/export_research_surfaces.py`
- `python3 scripts/export_repository_pulse.py`
- `python3 scripts/export_repository_growth.py`
- `python3 scripts/export_benchmark_surfaces.py`
- `python3 scripts/export_cymatic_surface.py`
- `python3 scripts/export_music_observatory.py`
- `python3 scripts/export_operator_surfaces.py`
- `python3 scripts/export_industry_profiles.py`
- `python3 scripts/export_industrial_diagnostics.py`
- `python3 scripts/export_edge_topology.py`
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
- `Repository growth export` · present · `proof/repository-growth.json`
- `Execution journal export` · present · `proof/execution-journal.json`
- `Cymatic surface export` · present · `proof/cymatic-surface.json`
- `Music observatory export` · present · `proof/music-observatory.json`
- `Privacy membrane export` · present · `proof/privacy-membrane.json`
- `Operator surfaces export` · present · `proof/operator-surfaces.json`
- `Industry profiles export` · present · `proof/industry-profiles.json`
- `Industrial diagnostics export` · present · `proof/industrial-diagnostics.json`
- `Edge topology export` · present · `proof/edge-topology.json`
- `Deployment stack` · present · `containers/compose.yaml`
