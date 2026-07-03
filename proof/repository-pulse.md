# Repository Pulse

- Service: `advanced-multimodal-ai`
- Version: `0.5.0`
- Readiness posture: `review_ready`
- Route count: `64`
- Test count: `36`
- Model count: `4`

## Lane status

### Frontend atlas

- Lane id: `frontend_atlas`
- Emphasis: `frontend`
- Live score: `100`
- Active count: `8`
- Warning count: `0`

The public site stays downstream from generated proof and research exports rather than inventing its own runtime story.

Files:
- `index.html`
- `advanced-technical-portfolio.html`
- `technical-portfolio.html`
- `model-observatory.html`
- `field-notes.html`
- `research-surfaces.js`
- `site-controls.css`
- `site-controls.js`

Artifacts:
- `index.html` · pass · 97329 bytes · updated 2026-07-03T08:02:52.932781+00:00
- `advanced-technical-portfolio.html` · pass · 21404 bytes · updated 2026-07-03T08:03:14.048962+00:00
- `technical-portfolio.html` · pass · 21010 bytes · updated 2026-07-03T07:32:54.992093+00:00
- `model-observatory.html` · pass · 12782 bytes · updated 2026-07-03T07:30:37.912441+00:00
- `field-notes.html` · pass · 10385 bytes · updated 2026-07-03T07:31:25.437631+00:00
- `research-surfaces.js` · pass · 1984 bytes · updated 2026-07-03T08:02:21.445648+00:00
- `site-controls.css` · pass · 2877 bytes · updated 2026-07-03T07:06:27.308506+00:00
- `site-controls.js` · pass · 3924 bytes · updated 2026-07-03T07:06:49.119232+00:00

Suggested actions:
- Keep the browser lane reading generated evidence files.
- Prefer live bundle hydration over static text repetition.


### Runtime backend

- Lane id: `runtime_backend`
- Emphasis: `backend`
- Live score: `100`
- Active count: `375`
- Warning count: `0`

64 routes, 36 tests, and persisted governance stores keep the API lane active.

Files:
- `src/advanced_multimodal_ai/api.py`
- `src/advanced_multimodal_ai/service.py`
- `src/advanced_multimodal_ai/connectors.py`
- `src/advanced_multimodal_ai/pipelines.py`
- `src/advanced_multimodal_ai/quality.py`
- `src/advanced_multimodal_ai/stewardship_store.py`
- `src/advanced_multimodal_ai/repository_pulse.py`

Artifacts:
- `src/advanced_multimodal_ai/api.py` · pass · 15241 bytes · updated 2026-07-03T07:58:21.936861+00:00
- `src/advanced_multimodal_ai/service.py` · pass · 50465 bytes · updated 2026-07-03T07:59:35.060927+00:00
- `src/advanced_multimodal_ai/connectors.py` · pass · 25293 bytes · updated 2026-07-03T06:41:33.072546+00:00
- `src/advanced_multimodal_ai/pipelines.py` · pass · 2102 bytes · updated 2026-07-03T04:37:14.847767+00:00
- `src/advanced_multimodal_ai/quality.py` · pass · 5294 bytes · updated 2026-07-03T04:05:08.862320+00:00
- `src/advanced_multimodal_ai/stewardship_store.py` · pass · 8754 bytes · updated 2026-07-03T06:55:10.293095+00:00
- `src/advanced_multimodal_ai/repository_pulse.py` · pass · 10694 bytes · updated 2026-07-03T07:59:22.281998+00:00

Suggested actions:
- Keep connector and replay evidence accumulating under varied inputs.
- Let governance stores grow beside active route traces.


### Compiled core

- Lane id: `compiled_core`
- Emphasis: `compiled`
- Live score: `67`
- Active count: `2`
- Warning count: `1`

Deterministic signal work stays in a compiled lane and remains reachable through a small Python bridge.

Files:
- `crates/multimodal-core/Cargo.toml`
- `crates/multimodal-core/src/lib.rs`
- `src/advanced_multimodal_ai/rust_bridge.py`

Artifacts:
- `crates/multimodal-core/Cargo.toml` · pass · 331 bytes · updated 2026-07-03T04:54:07.954729+00:00
- `crates/multimodal-core/src/lib.rs` · missing · 0 bytes
- `src/advanced_multimodal_ai/rust_bridge.py` · pass · 2355 bytes · updated 2026-07-03T04:55:09.251387+00:00

Suggested actions:
- Keep the compiled lane narrow and measured.
- Add new Rust only where deterministic math or replay earns it.


### Generated clients

- Lane id: `generated_clients`
- Emphasis: `client`
- Live score: `100`
- Active count: `4`
- Warning count: `0`

The Python and TypeScript client surfaces are generated from the live contract rather than maintained as parallel lore.

Files:
- `openapi/openapi.json`
- `sdk/python/src/advanced_multimodal_ai_client/generated_openapi.py`
- `sdk/typescript/src/generated-openapi.ts`
- `sdk/typescript/package.json`

Artifacts:
- `openapi/openapi.json` · pass · 112591 bytes · updated 2026-07-03T08:10:16.600022+00:00
- `sdk/python/src/advanced_multimodal_ai_client/generated_openapi.py` · pass · 14571 bytes · updated 2026-07-03T08:10:34.730672+00:00
- `sdk/typescript/src/generated-openapi.ts` · pass · 17810 bytes · updated 2026-07-03T08:10:34.729777+00:00
- `sdk/typescript/package.json` · pass · 613 bytes · updated 2026-07-03T07:03:48.596897+00:00

Suggested actions:
- Regenerate client surfaces whenever the API contract moves.
- Keep TypeScript compilation in the proof path.


### Evidence exports

- Lane id: `evidence_exports`
- Emphasis: `evidence`
- Live score: `100`
- Active count: `10`
- Warning count: `0`

Proof, readiness, worked examples, and research surfaces can be regenerated as files the public site reads directly.

Files:
- `proof/runtime-proof.json`
- `proof/readiness-report.json`
- `proof/example-bundle.json`
- `proof/research-surfaces.json`
- `proof/execution-journal.json`
- `scripts/build_runtime_proof_bundle.py`
- `scripts/export_execution_journal.py`
- `scripts/export_readiness_report.py`
- `scripts/export_example_bundle.py`
- `scripts/export_research_surfaces.py`

Artifacts:
- `proof/runtime-proof.json` · pass · 3544 bytes · updated 2026-07-03T08:12:01.417255+00:00
- `proof/readiness-report.json` · pass · 2846 bytes · updated 2026-07-03T08:11:44.147556+00:00
- `proof/example-bundle.json` · pass · 2602 bytes · updated 2026-07-03T08:12:18.973218+00:00
- `proof/research-surfaces.json` · pass · 25985 bytes · updated 2026-07-03T08:11:05.475333+00:00
- `proof/execution-journal.json` · pass · 8924 bytes · updated 2026-07-03T08:12:39.153687+00:00
- `scripts/build_runtime_proof_bundle.py` · pass · 3258 bytes · updated 2026-07-03T08:01:25.111055+00:00
- `scripts/export_execution_journal.py` · pass · 3170 bytes · updated 2026-07-03T08:01:44.421366+00:00
- `scripts/export_readiness_report.py` · pass · 2849 bytes · updated 2026-07-03T08:01:24.963842+00:00
- `scripts/export_example_bundle.py` · pass · 18403 bytes · updated 2026-07-03T08:09:50.090499+00:00
- `scripts/export_research_surfaces.py` · pass · 6323 bytes · updated 2026-07-03T08:01:25.400015+00:00

Suggested actions:
- Keep exports close to CI and local verification.
- Prefer regenerated artifacts to hand-edited summaries.


### Execution history

- Lane id: `execution_history`
- Emphasis: `evidence`
- Live score: `90`
- Active count: `10`
- Warning count: `0`

10 persisted script runs now leave a reusable memory of what exported, what passed, and what files changed.

Files:
- `src/advanced_multimodal_ai/execution_journal.py`
- `src/advanced_multimodal_ai/execution_journal_store.py`
- `proof/execution-journal.json`
- `proof/execution-journal.md`

Artifacts:
- `src/advanced_multimodal_ai/execution_journal.py` · pass · 3025 bytes · updated 2026-07-03T07:57:44.389341+00:00
- `src/advanced_multimodal_ai/execution_journal_store.py` · pass · 5238 bytes · updated 2026-07-03T08:04:38.170459+00:00
- `proof/execution-journal.json` · pass · 8924 bytes · updated 2026-07-03T08:12:39.153687+00:00
- `proof/execution-journal.md` · pass · 3578 bytes · updated 2026-07-03T08:12:39.153860+00:00

Suggested actions:
- Let export and verification lanes keep writing their own receipts.
- Use repeated runs to show operational continuity, not one-time polish.


### Model registry

- Lane id: `model_registry`
- Emphasis: `models`
- Live score: `55`
- Active count: `4`
- Warning count: `4`

0 of 4 named models are runtime-ready in the current environment.

Files:
- `complete_model.py`
- `core/attention_mechanisms.py`
- `dynamic_transformer.py`
- `fusion_strategies.py`

Artifacts:
- `complete_model.py` · pass · 60066 bytes · updated 2026-07-03T01:23:50.575757+00:00
- `core/attention_mechanisms.py` · pass · 30134 bytes · updated 2026-07-03T01:23:50.576058+00:00
- `dynamic_transformer.py` · pass · 54214 bytes · updated 2026-07-03T01:23:50.576273+00:00
- `fusion_strategies.py` · pass · 25665 bytes · updated 2026-07-03T01:23:50.576436+00:00

Suggested actions:
- Promote research models only when proof and replay back them.
- Keep model notes honest about what is live and what is still exploratory.

