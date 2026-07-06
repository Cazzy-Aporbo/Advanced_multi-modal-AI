# Repository File Map

- Service: `advanced-multimodal-ai`
- Version: `0.5.0`
- Files mapped: `174`
- Edges mapped: `1043`
- Active Python files: `99`
- Frontend files: `21`
- Proof files: `34`

## Lane counts

- `audio warehouse`: `5`
- `compiled signal core`: `2`
- `data movement`: `4`
- `documentation`: `12`
- `export and proof`: `21`
- `generated evidence`: `34`
- `industrial diagnostics`: `15`
- `privacy membrane`: `2`
- `public interface`: `21`
- `research surfaces`: `6`
- `risk and drift`: `4`
- `runtime composition`: `2`
- `runtime support`: `40`
- `verification`: `6`

## Language counts

- `HTML`: `12`
- `JSON`: `17`
- `JavaScript`: `9`
- `Markdown`: `29`
- `Python`: `105`
- `Rust`: `2`

## Most connected files

### `index.html`

- Lane: `public interface`
- Language: `HTML`
- Status: `frontend`
- Complexity score: `100`
- Lines: `3759`
- Routes: `0`
- Tests: `0`

Renders the Advanced Multi-modal AI · Signal Atlas public surface.

Inputs:
- Arrow or Parquet tables
- local persisted runtime records
- generated proof JSON or live API payloads
- 32 referenced file connections

Outputs:
- interactive browser surface
- queryable runtime store rows
- read by 16 repository files

Connects to:
- `CONTRIBUTING.md`
- `README.md`
- `SECURITY.md`
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `cymatic-surface.js`
- `field-notes.html`

Imported by:
- `README.md`
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `field-notes.html`
- `industrial-diagnostics.html`
- `industry-profiles.html`
- `model-observatory.html`

Evidence:
- writes or reads proof files


### `src/advanced_multimodal_ai/service.py`

- Lane: `runtime composition`
- Language: `Python`
- Status: `active`
- Complexity score: `100`
- Lines: `2404`
- Routes: `0`
- Tests: `0`

Supports the runtime composition lane.

Inputs:
- Arrow or Parquet tables
- 56 referenced file connections

Outputs:
- schema-checked payloads
- read by 17 repository files

Connects to:
- `proof/runtime-proof.json`
- `src/advanced_multimodal_ai/alignment.py`
- `src/advanced_multimodal_ai/attestation.py`
- `src/advanced_multimodal_ai/bias_taxonomy.py`
- `src/advanced_multimodal_ai/catalog.py`
- `src/advanced_multimodal_ai/catalog_store.py`
- `src/advanced_multimodal_ai/config.py`
- `src/advanced_multimodal_ai/connector_store.py`

Imported by:
- `CLAUDE.md`
- `docs/REPOSITORY_LANES.md`
- `proof/cymatic-surface.md`
- `proof/operator-surfaces.md`
- `proof/repository-file-map.md`
- `proof/repository-pulse.md`
- `proof/research-surfaces.md`
- `src/advanced_multimodal_ai/api.py`

Evidence:
- test-linked
- writes or reads proof files


### `model-observatory.html`

- Lane: `public interface`
- Language: `HTML`
- Status: `frontend`
- Complexity score: `100`
- Lines: `1535`
- Routes: `0`
- Tests: `0`

Renders the Advanced Multi-modal AI · Model Observatory public surface.

Inputs:
- 15 referenced file connections

Outputs:
- interactive browser surface
- read by 17 repository files

Connects to:
- `README.md`
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `field-notes.html`
- `index.html`
- `industry-profiles.html`
- `music-observatory.html`

Imported by:
- `README.md`
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `field-notes.html`
- `index.html`
- `industry-profiles.html`
- `music-observatory.html`

Evidence:
- writes or reads proof files


### `benchmark-observatory.html`

- Lane: `public interface`
- Language: `HTML`
- Status: `frontend`
- Complexity score: `100`
- Lines: `910`
- Routes: `0`
- Tests: `0`

Renders the Advanced Multi-modal AI · Benchmark Observatory public surface.

Inputs:
- 13 referenced file connections

Outputs:
- interactive browser surface
- read by 14 repository files

Connects to:
- `README.md`
- `advanced-technical-portfolio.html`
- `cymatic-media-engine.html`
- `field-notes.html`
- `index.html`
- `industry-profiles.html`
- `model-observatory.html`
- `music-observatory.html`

Imported by:
- `advanced-technical-portfolio.html`
- `cymatic-media-engine.html`
- `field-notes.html`
- `index.html`
- `industry-profiles.html`
- `model-observatory.html`
- `music-observatory.html`
- `research-surfaces.js`

Evidence:
- writes or reads proof files


### `music-observatory.html`

- Lane: `public interface`
- Language: `HTML`
- Status: `frontend`
- Complexity score: `100`
- Lines: `743`
- Routes: `0`
- Tests: `0`

Renders the Advanced Multi-modal AI · Music Observatory public surface.

Inputs:
- 13 referenced file connections

Outputs:
- interactive browser surface
- read by 18 repository files

Connects to:
- `README.md`
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `index.html`
- `industry-profiles.html`
- `model-observatory.html`
- `music-observatory.js`

Imported by:
- `README.md`
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `cymatic-surface.js`
- `field-notes.html`
- `index.html`
- `industry-profiles.html`

Evidence:
- writes or reads proof files


### `technical-portfolio.html`

- Lane: `public interface`
- Language: `HTML`
- Status: `frontend`
- Complexity score: `100`
- Lines: `624`
- Routes: `0`
- Tests: `0`

Renders the Advanced Multi-modal AI · Component Catalog public surface.

Inputs:
- Arrow or Parquet tables
- local persisted runtime records
- 14 referenced file connections

Outputs:
- interactive browser surface
- queryable runtime store rows
- read by 14 repository files

Connects to:
- `README.md`
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `field-notes.html`
- `index.html`
- `industry-profiles.html`
- `model-observatory.html`

Imported by:
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `field-notes.html`
- `index.html`
- `industrial-diagnostics.html`
- `industry-profiles.html`
- `model-observatory.html`

Evidence:
- static repository evidence


### `advanced-technical-portfolio.html`

- Lane: `public interface`
- Language: `HTML`
- Status: `frontend`
- Complexity score: `100`
- Lines: `576`
- Routes: `0`
- Tests: `0`

Renders the Advanced Multi-modal AI · Architecture Surface public surface.

Inputs:
- Arrow or Parquet tables
- local persisted runtime records
- 14 referenced file connections

Outputs:
- interactive browser surface
- queryable runtime store rows
- read by 15 repository files

Connects to:
- `README.md`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `field-notes.html`
- `index.html`
- `industry-profiles.html`
- `model-observatory.html`
- `music-observatory.html`

Imported by:
- `CLAUDE.md`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `field-notes.html`
- `index.html`
- `industry-profiles.html`
- `model-observatory.html`
- `music-observatory.html`

Evidence:
- static repository evidence


### `README.md`

- Lane: `documentation`
- Language: `Markdown`
- Status: `supporting`
- Complexity score: `100`
- Lines: `509`
- Routes: `0`
- Tests: `0`

Documents repository use, contribution, security, or generated proof context.

Inputs:
- Arrow or Parquet tables
- local persisted runtime records
- 23 referenced file connections

Outputs:
- queryable runtime store rows
- read by 14 repository files

Connects to:
- `docs/GROUNDING_AND_BOUNDARIES.md`
- `docs/engineering-journal.md`
- `examples/diesel_engine.py`
- `examples/electrical_system.py`
- `examples/hydraulic_system.py`
- `growth-surface.js`
- `index.html`
- `industrial-diagnostics.html`

Imported by:
- `CLAUDE.md`
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `field-notes.html`
- `index.html`
- `industrial-diagnostics.html`
- `industry-profiles.html`

Evidence:
- writes or reads proof files


### `field-notes.html`

- Lane: `public interface`
- Language: `HTML`
- Status: `frontend`
- Complexity score: `100`
- Lines: `448`
- Routes: `0`
- Tests: `0`

Renders the Advanced Multi-modal AI · Field Notes public surface.

Inputs:
- 14 referenced file connections

Outputs:
- interactive browser surface
- read by 12 repository files

Connects to:
- `README.md`
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `index.html`
- `industry-profiles.html`
- `model-observatory.html`
- `music-observatory.html`

Imported by:
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `index.html`
- `industry-profiles.html`
- `model-observatory.html`
- `src/advanced_multimodal_ai/cymatic_surface.py`
- `src/advanced_multimodal_ai/operator_surfaces.py`

Evidence:
- writes or reads proof files


### `cymatic-media-engine.html`

- Lane: `public interface`
- Language: `HTML`
- Status: `frontend`
- Complexity score: `100`
- Lines: `438`
- Routes: `0`
- Tests: `0`

Renders the Advanced Multi-modal AI · Cymatic Media Engine public surface.

Inputs:
- 15 referenced file connections

Outputs:
- interactive browser surface
- read by 10 repository files

Connects to:
- `README.md`
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-surface.js`
- `field-notes.html`
- `index.html`
- `industry-profiles.html`
- `model-observatory.html`

Imported by:
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `field-notes.html`
- `index.html`
- `model-observatory.html`
- `music-observatory.html`
- `src/advanced_multimodal_ai/repository_growth.py`
- `src/advanced_multimodal_ai/repository_pulse.py`

Evidence:
- writes or reads proof files


### `industry-profiles.html`

- Lane: `public interface`
- Language: `HTML`
- Status: `frontend`
- Complexity score: `94`
- Lines: `467`
- Routes: `0`
- Tests: `0`

Renders the Advanced Multi-modal AI · Industry Profiles public surface.

Inputs:
- 10 referenced file connections

Outputs:
- interactive browser surface
- read by 11 repository files

Connects to:
- `README.md`
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `field-notes.html`
- `index.html`
- `industry-profiles.js`
- `model-observatory.html`
- `music-observatory.html`

Imported by:
- `advanced-technical-portfolio.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `field-notes.html`
- `index.html`
- `industrial-diagnostics.html`
- `model-observatory.html`
- `music-observatory.html`

Evidence:
- static repository evidence


### `proof/research-surfaces.md`

- Lane: `generated evidence`
- Language: `Markdown`
- Status: `proof`
- Complexity score: `100`
- Lines: `876`
- Routes: `0`
- Tests: `0`

Stores a generated proof surface read by the public atlas and review workflows.

Inputs:
- live FastAPI route responses
- Arrow or Parquet tables
- export script output
- 49 referenced file connections

Outputs:
- versioned proof artifacts
- read by 8 repository files

Connects to:
- `proof/benchmark-surfaces.json`
- `proof/benchmark-surfaces.md`
- `proof/cymatic-surface.json`
- `proof/music-observatory.json`
- `proof/readiness-report.json`
- `proof/research-surfaces.json`
- `proof/runtime-proof.json`
- `scripts/build_runtime_proof_bundle.py`

Imported by:
- `cymatic-media-engine.html`
- `field-notes.html`
- `index.html`
- `model-observatory.html`
- `proof/execution-journal.md`
- `proof/repository-file-map.md`
- `scripts/export_research_surfaces.py`
- `src/advanced_multimodal_ai/research_influence.py`

Evidence:
- generated artifact
- writes or reads proof files

