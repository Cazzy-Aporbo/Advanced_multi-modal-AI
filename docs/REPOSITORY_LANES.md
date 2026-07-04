# Repository Lanes

The repository has one public face, but it does not operate as one blurred codebase.
Each lane has a narrower purpose, a small set of files, and a clearer review path.

## Public surface

This lane is for reading, comparing, and exploring generated evidence.

- `index.html`
- `advanced-technical-portfolio.html`
- `technical-portfolio.html`
- `model-observatory.html`
- `music-observatory.html`
- `industry-profiles.html`
- `benchmark-observatory.html`
- `field-notes.html`
- `cymatic-media-engine.html`
- `research-surfaces.js`
- `growth-surface.js`
- `music-observatory.js`
- `industry-profiles.js`
- `site-controls.css`
- `site-controls.js`
- `cymatic-surface.css`
- `cymatic-surface.js`

What belongs here:

- reading exported proof
- guiding a reader through the runtime lanes
- translating signals into a calmer visual language
- local browser interactivity that does not replace backend evidence

What does not belong here:

- inference orchestration
- connector intake
- persistence policy
- ledger generation

## Runtime backend

This lane owns the application contracts and the durable execution path.

- `src/advanced_multimodal_ai/api.py`
- `src/advanced_multimodal_ai/service.py`
- `src/advanced_multimodal_ai/connectors.py`
- `src/advanced_multimodal_ai/pipelines.py`
- `src/advanced_multimodal_ai/quality.py`
- `src/advanced_multimodal_ai/replay.py`
- `src/advanced_multimodal_ai/benchmarks.py`
- `src/advanced_multimodal_ai/governance_ledger.py`
- `src/advanced_multimodal_ai/edge_gateway.py`
- `src/advanced_multimodal_ai/industry_profiles.py`
- `src/advanced_multimodal_ai/music_features.py`
- `src/advanced_multimodal_ai/music_queries.py`
- `src/advanced_multimodal_ai/music_truth.py`
- `src/advanced_multimodal_ai/operator_surfaces.py`
- `src/advanced_multimodal_ai/repository_growth.py`
- `src/advanced_multimodal_ai/repository_pulse.py`
- `src/advanced_multimodal_ai/research_surfaces.py`
- `src/advanced_multimodal_ai/tracking_ledger.py`
- `src/advanced_multimodal_ai/vector_mesh.py`

What belongs here:

- typed request and response contracts
- connector-backed ingest
- data quality and temporal alignment
- replay, provenance, and benchmark execution
- compliance and execution memory
- manifest-only audio declarations and derived feature warehousing
- domain transfer profiles tied to live routes rather than prose alone
- operator, pulse, and edge-topology exports fed from the same service layer

## Compiled lane

This lane stays narrow on purpose.

- `crates/multimodal-core/`
- `src/advanced_multimodal_ai/rust_bridge.py`

It holds deterministic work that benefits from a compiled path:

- tensor signatures
- transcript-led video cut logic
- low-level signal routines that should not live as loose Python helpers forever

## Generated contracts and clients

This lane exists so downstream integrations do not have to infer the API from prose.

- `openapi/openapi.json`
- `sdk/python/`
- `sdk/typescript/`

The generated clients should move with the live contract, not drift into parallel lore.

## Proof and execution memory

This lane keeps the public surface anchored.

- `proof/`
- `scripts/export_*.py`
- `scripts/build_runtime_proof_bundle.py`
- `scripts/run_acceptance_spine.py`

The browser pages should remain downstream from these artifacts. If a proof export changes,
the public pages should read the new file rather than invent a new explanation.

## Community and trust surface

This lane reduces contribution friction and keeps repository signals grounded in
the same evidence discipline as the runtime.

- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/use_case.yml`
- `.github/pull_request_template.md`
- `proof/repository-growth.json`
- `proof/repository-growth.md`
- `scripts/export_repository_growth.py`
- `proof/industrial-diagnostics.json`
- `proof/industrial-diagnostics.md`
- `scripts/export_industrial_diagnostics.py`

What belongs here:

- contribution guidance tied back to tests, routes, and proof exports
- repository signal snapshots kept beside route and proof counts
- security reporting instructions that fit the actual runtime

What does not belong here:

- vanity claims without live measurements
- open-ended calls for help with no review path

## Archive experiments

This lane keeps executable studies that still matter without pretending they are
part of the narrow runtime edge.

- `Advanced_/microscopic_signal_pathways.py`
- `complete_model.py`
- `dynamic_transformer.py`
- `fusion_strategies.py`
- `core/attention_mechanisms.py`

What belongs here:

- direct experiments that help explain why the runtime lanes exist
- model work that remains useful for learning, comparison, or future reduction
- smaller Python studies that replace notebook state with executable files

What does not belong here:

- public proof claims without a route back to runtime evidence
- half-finished browser copy standing in for backend behavior
