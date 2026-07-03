# Repository Lanes

The repository has one public face, but it does not operate as one blurred codebase.
Each lane has a narrower purpose, a small set of files, and a clearer review path.

## Public surface

This lane is for reading, comparing, and exploring generated evidence.

- `index.html`
- `advanced-technical-portfolio.html`
- `technical-portfolio.html`
- `model-observatory.html`
- `benchmark-observatory.html`
- `field-notes.html`
- `cymatic-media-engine.html`
- `research-surfaces.js`
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

What belongs here:

- typed request and response contracts
- connector-backed ingest
- data quality and temporal alignment
- replay, provenance, and benchmark execution
- compliance and execution memory

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
