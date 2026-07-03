# CLAUDE.md

## Project posture

Advanced Multi-modal AI is a polyglot runtime and research repository. The
service edge, stores, contracts, and generated artifacts should remain small
enough to verify directly. New work should widen evidence, not widen theatre.

## Working rules

- Start with the persisted runtime under `src/advanced_multimodal_ai/`.
- Keep public pages downstream of the backend. Update HTML, README, OpenAPI, and
  generated SDKs after the API surface changes.
- Prefer typed contracts and persisted records over loose example prose.
- Treat lifecycle, provenance, drift, and supply-chain work as first-class
  engineering surfaces rather than documentation-only ideas.

## Commands

```bash
python3 -m ruff check src tests
python3 -m pytest -q
cargo test -p multimodal-core
python3 scripts/export_openapi.py
python3 scripts/generate_sdk_surfaces.py
python3 scripts/export_readiness_report.py
python3 scripts/export_example_bundle.py
python3 scripts/build_runtime_proof_bundle.py
python3 scripts/run_acceptance_spine.py
npm run --prefix sdk/typescript check
```

## Change discipline

- If an endpoint changes, regenerate OpenAPI and both SDK surfaces.
- If a store changes, update `sql/runtime_schema.sql`.
- If a public claim changes, make sure `README.md` and
  `advanced-technical-portfolio.html` still describe only what the code proves.
- Avoid adding synthetic traffic generators, decorative architecture claims, or
  copy that promises hidden infrastructure.

## Useful file map

```text
src/advanced_multimodal_ai/api.py                 FastAPI routes
src/advanced_multimodal_ai/service.py             runtime coordination
src/advanced_multimodal_ai/contracts.py           typed request and response schemas
src/advanced_multimodal_ai/stewardship_store.py   lifecycle, change, and supply records
src/advanced_multimodal_ai/connectors.py          file, object-store, HTTP, and public web intake
src/advanced_multimodal_ai/readiness.py           review posture assembly
sql/runtime_schema.sql                            persisted table contract
```
