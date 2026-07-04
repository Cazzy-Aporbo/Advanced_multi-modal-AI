# Advanced Multi-modal AI

<p align="left">
  <a href="https://www.python.org/">
    <img alt="Python runtime edge" src="https://img.shields.io/badge/Python-runtime%20edge-8fb8ff?style=for-the-badge&labelColor=171923">
  </a>
  <a href="https://www.rust-lang.org/">
    <img alt="Rust compiled core" src="https://img.shields.io/badge/Rust-compiled%20core-f2ad7a?style=for-the-badge&labelColor=171923">
  </a>
  <a href="https://www.typescriptlang.org/">
    <img alt="TypeScript SDK" src="https://img.shields.io/badge/TypeScript-SDK-92d6cf?style=for-the-badge&labelColor=171923">
  </a>
  <a href="./openapi/openapi.json">
    <img alt="OpenAPI generated contract" src="https://img.shields.io/badge/OpenAPI-generated-f0b7d3?style=for-the-badge&labelColor=171923">
  </a>
  <a href="./LICENSE">
    <img alt="Apache 2.0" src="https://img.shields.io/badge/License-Apache%202.0-f3d27c?style=for-the-badge&labelColor=171923">
  </a>
</p>

<p>
  A multimodal systems repository for cleaning, aligning, profiling, testing,
  and explaining signals before they become model output. It keeps the work
  visible: contracts, proof exports, generated clients, replay records, derived
  audio features, industry transfer profiles, and deterministic industrial
  diagnostics all sit beside the code that creates them.
</p>

<p>
  The public pages are not separate marketing pages. They read generated files
  from <a href="./proof">proof/</a>, so the visible story remains tied to the
  runtime.
</p>

<table>
  <tr>
    <td width="20%" valign="top"><strong>Runtime</strong><br/>FastAPI contracts, persistence, replay, inference, retrieval, jobs.</td>
    <td width="20%" valign="top"><strong>Signals</strong><br/>Audio features, tensor profiles, temporal windows, cross-modal alignment.</td>
    <td width="20%" valign="top"><strong>Proof</strong><br/>OpenAPI, readiness, benchmark, execution journal, generated bundles.</td>
    <td width="20%" valign="top"><strong>Safety</strong><br/>Drift checks, provenance, supply chain, bias taxonomy, edge review.</td>
    <td width="20%" valign="top"><strong>Field Work</strong><br/>Industrial fault reasoning, compliance checks, formal restart logic.</td>
  </tr>
</table>

<table>
  <tr>
    <td width="33%" valign="top">
      <strong>Start visually</strong><br/>
      <sub>Architecture, models, music, industry lanes, and diagnostics.</sub><br/><br/>
      <a href="https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/Advanced_multi-modal-AI/blob/main/index.html">Open the Signal Atlas</a>
    </td>
    <td width="33%" valign="top">
      <strong>Start from code</strong><br/>
      <sub>Run the API, tests, proof exports, and generated clients.</sub><br/><br/>
      <a href="#quick-start">Quick start</a>
    </td>
    <td width="33%" valign="top">
      <strong>Start from evidence</strong><br/>
      <sub>Read the generated proof bundle before reading the claims.</sub><br/><br/>
      <a href="./proof/runtime-proof.md">Runtime proof</a> ·
      <a href="./proof/readiness-report.md">Readiness</a>
    </td>
  </tr>
</table>

## Surfaces

<table>
  <tr>
    <td width="25%" valign="top">
      <strong>Signal Atlas</strong><br/>
      <sub>Front door for the repo.</sub><br/>
      <a href="https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/Advanced_multi-modal-AI/blob/main/index.html">open</a>
    </td>
    <td width="25%" valign="top">
      <strong>Architecture</strong><br/>
      <sub>Runtime lanes and contracts.</sub><br/>
      <a href="https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/Advanced_multi-modal-AI/blob/main/advanced-technical-portfolio.html">open</a>
    </td>
    <td width="25%" valign="top">
      <strong>Catalog</strong><br/>
      <sub>Files, models, generated clients.</sub><br/>
      <a href="https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/Advanced_multi-modal-AI/blob/main/technical-portfolio.html">open</a>
    </td>
    <td width="25%" valign="top">
      <strong>Models</strong><br/>
      <sub>Model cards and open questions.</sub><br/>
      <a href="https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/Advanced_multi-modal-AI/blob/main/model-observatory.html">open</a>
    </td>
  </tr>
  <tr>
    <td width="25%" valign="top">
      <strong>Benchmarks</strong><br/>
      <sub>Reference runs and replay ledger.</sub><br/>
      <a href="https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/Advanced_multi-modal-AI/blob/main/benchmark-observatory.html">open</a>
    </td>
    <td width="25%" valign="top">
      <strong>Music Warehouse</strong><br/>
      <sub>Manifest-only audio lane and drift proof.</sub><br/>
      <a href="https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/Advanced_multi-modal-AI/blob/main/music-observatory.html">open</a>
    </td>
    <td width="25%" valign="top">
      <strong>Industry Profiles</strong><br/>
      <sub>Domain routes tied to live endpoints.</sub><br/>
      <a href="https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/Advanced_multi-modal-AI/blob/main/industry-profiles.html">open</a>
    </td>
    <td width="25%" valign="top">
      <strong>Industrial Diagnostics</strong><br/>
      <sub>Fault graph, compliance, restart checks.</sub><br/>
      <a href="https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/Advanced_multi-modal-AI/blob/main/industrial-diagnostics.html">open</a>
    </td>
  </tr>
</table>

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]

uvicorn advanced_multimodal_ai.api:create_app --factory --host 0.0.0.0 --port 8000
```

Open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/v1/health`
- `http://127.0.0.1:8000/metrics`

Run the local gate:

```bash
python3 -m pytest -q
python3 -m ruff check src tests scripts
cargo test -p multimodal-core
npm run --prefix sdk/typescript check
make proof
make acceptance
```

<details>
  <summary><strong>What runs today</strong></summary>

| Lane | Runtime surface | Evidence |
| --- | --- | --- |
| API and contracts | `src/advanced_multimodal_ai/api.py`, `contracts.py`, `service.py` | `openapi/openapi.json`, generated Python and TypeScript clients |
| Ingestion | typed local, HTTP, public-web, CSV, NDJSON, Parquet, and S3-shaped connectors | connector run records, catalog fingerprints, pipeline replay |
| Music features | manifest-only audio intake, segment index, feature warehouse, embeddings, drift | `proof/music-observatory.*`, `/v1/music/*` |
| Industrial diagnostics | symbolic fault rules, safety checks, formal transition review, fault graph | `proof/industrial-diagnostics.*`, `/v1/industrial/*` |
| Edge review | packet scoring, policy profile, ledger entries, topology export | `proof/edge-topology.*`, `/v1/edge/*` |
| Research surfaces | model cards, findings, connection map, operator surfaces | `proof/research-surfaces.*`, `proof/operator-surfaces.*` |
| Growth and adoption hygiene | issue templates, contribution path, proof freshness, repository snapshot | `proof/repository-growth.*`, `growth-surface.js` |

</details>

<details>
  <summary><strong>Runtime map</strong></summary>

The repository is split by responsibility.

| Lane | Primary files | Job |
| --- | --- | --- |
| Public pages | `index.html`, `model-observatory.html`, `music-observatory.html`, `industrial-diagnostics.html` | render generated proof and guide reading |
| Backend | `src/advanced_multimodal_ai/` | validate contracts, run analysis, persist records, expose API |
| Compiled core | `crates/multimodal-core/` | deterministic tensor signatures and transcript-led cut logic |
| SDKs | `sdk/python`, `sdk/typescript` | generated client surfaces from the live OpenAPI app |
| Proof exports | `proof/`, `scripts/export_*.py` | static evidence for pages, docs, and review |
| Runtime memory | `.runtime/` | local SQLite stores for jobs, catalogs, recipes, ledgers, and journals |

The flow is:

```text
connector or request
  -> dataset contract
  -> quality and provenance
  -> alignment, drift, replay, or inference
  -> proof export
  -> public surface
```

</details>

<details>
  <summary><strong>API groups</strong></summary>

| Group | Routes |
| --- | --- |
| Runtime | `/v1/health`, `/v1/ready`, `/v1/runtime/attestation`, `/v1/runtime/compliance-ledger`, `/v1/readiness/report` |
| Catalog and connectors | `/v1/catalog/*`, `/v1/connectors/*`, `/v1/pipelines/*` |
| Models and inference | `/v1/models`, `/v1/plan`, `/v1/infer`, `/v1/stream`, `/v1/retrieval/*` |
| Data review | `/v1/data/profile`, `/v1/data/provenance`, `/v1/alignment/windows`, `/v1/drift/*` |
| Music | `/v1/music/manifests`, `/v1/music/features/*`, `/v1/music/drift`, `/v1/music/proof/change-report` |
| Video | `/v1/video/packet`, `/v1/video/clean`, `/v1/jobs/video-clean` |
| Governance and stewardship | `/v1/stewardship/*`, `/v1/ontology/*`, `/v1/bias/*`, `/v1/edge/*` |
| Industrial diagnostics | `/v1/industrial/scenarios`, `/v1/industrial/diagnose`, `/v1/industrial/model-check` |
| Proof and public research | `/v1/proof/bundle`, `/v1/research/*`, `/v1/operators/*`, `/v1/industries/profiles`, `/v1/repository/pulse`, `/v1/growth/snapshot` |

</details>

<details>
  <summary><strong>Music warehouse</strong></summary>

The music lane stores manifests and derived features, not raw tracks.

| Layer | What is kept |
| --- | --- |
| Manifest | `track_id`, `source_uri`, `sha256`, license, duration, region, language, split, provenance |
| Segment index | `start_ms`, `end_ms`, speaker or section, transcript reference, quality flags |
| Feature rows | RMS, silence ratio, onset density, tempo proxy, beat stability, spectral features, MFCC-like summaries, chroma summaries, key confidence, repetition density, dynamic crest |
| Embedding rows | vector, model name, extraction date, contract hash |
| Drift | loudness, language share, genre imbalance, repetition, silence padding, production polish, regional undercoverage |

Useful surfaces:

- `POST /v1/music/features/extract`
- `GET /v1/music/snapshot`
- `GET /v1/music/drift`
- `GET /v1/music/proof/change-report`
- [`proof/music-observatory.md`](./proof/music-observatory.md)

</details>

<details>
  <summary><strong>Industrial diagnostics</strong></summary>

The industrial lane is a bounded diagnostic engine for field troubleshooting.
It keeps technician reports, sensor thresholds, safety checks, state
transitions, and final verdicts in one inspectable response.

| Layer | Files |
| --- | --- |
| Symbolic rules | `industrial_diagnostics/deterministic_engine/symbolic_reasoner.py` |
| Formal trace | `industrial_diagnostics/deterministic_engine/formal_spec.py` |
| Model checking | `industrial_diagnostics/deterministic_engine/model_checking.py` |
| Compliance checks | `industrial_diagnostics/compliance/osha_1910.py`, `iso_13849.py`, `iec_61508.py` |
| Explainability | `industrial_diagnostics/explainability/proof_tree.py`, `audit_trail.py`, `fault_graph.py` |
| Examples | `examples/diesel_engine.py`, `examples/hydraulic_system.py`, `examples/electrical_system.py` |

Useful surfaces:

- `GET /v1/industrial/scenarios`
- `POST /v1/industrial/diagnose`
- `POST /v1/industrial/model-check`
- [`proof/industrial-diagnostics.md`](./proof/industrial-diagnostics.md)
- [`industrial-diagnostics.html`](./industrial-diagnostics.html)

</details>

<details>
  <summary><strong>Repository layout</strong></summary>

```text
Advanced_multi-modal-AI/
├── index.html
├── advanced-technical-portfolio.html
├── technical-portfolio.html
├── model-observatory.html
├── benchmark-observatory.html
├── music-observatory.html
├── industry-profiles.html
├── industrial-diagnostics.html
├── field-notes.html
├── src/advanced_multimodal_ai/
│   ├── api.py
│   ├── contracts.py
│   ├── service.py
│   ├── connectors.py
│   ├── catalog.py
│   ├── quality.py
│   ├── provenance.py
│   ├── alignment.py
│   ├── drift.py
│   ├── music_features.py
│   ├── music_truth.py
│   ├── edge_gateway.py
│   ├── industrial_diagnostics/
│   └── repository_growth.py
├── crates/multimodal-core/
├── sdk/python/
├── sdk/typescript/
├── examples/
├── docs/
├── proof/
├── scripts/
├── containers/
├── Dockerfile
├── docker-compose.yml
├── CITATION.cff
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── LICENSE
└── NOTICE
```

</details>

<details>
  <summary><strong>How the Python files connect</strong></summary>

| Files | Connection |
| --- | --- |
| `connectors.py`, `catalog.py`, `connector_store.py`, `catalog_store.py` | bring data in, infer contracts, persist source evidence |
| `pipelines.py`, `quality.py`, `signal_math.py`, `alignment.py` | shape raw events into measured multimodal work |
| `contracts.py`, `service.py`, `api.py` | hold typed requests, coordinate runtime behavior, expose routes |
| `drift.py`, `domain_ontology.py`, `liability_surface.py`, `stewardship_store.py` | review population shifts, operational movement, lifecycle coverage, and route constraints |
| `music_features.py`, `music_embeddings.py`, `music_truth.py`, `music_store.py` | create derived audio feature lanes and catalog-level change proof |
| `industrial_diagnostics/` | diagnose machine faults, evaluate compliance posture, produce graph and audit proof |
| `attestation.py`, `proof.py`, `readiness.py`, `execution_journal.py` | export what exists, what ran, and what still needs coverage |

</details>

<details>
  <summary><strong>Generated proof files</strong></summary>

| File | Purpose |
| --- | --- |
| `proof/runtime-proof.md` | route, connector, verification, artifact, and store summary |
| `proof/readiness-report.md` | present-tense checks and boundaries |
| `proof/benchmark-surfaces.md` | benchmark and replay evidence |
| `proof/music-observatory.md` | music feature warehouse and drift evidence |
| `proof/industrial-diagnostics.md` | industrial scenario, proof tree, audit chain, compliance findings |
| `proof/industry-profiles.md` | domain transfer routes and proof surfaces |
| `proof/repository-growth.md` | repo health, contribution, proof freshness, and publishing signals |
| `proof/execution-journal.md` | export and verification history |

Regenerate the full set with:

```bash
make proof
```

</details>

<details>
  <summary><strong>OpenAPI, Rust, and SDKs</strong></summary>

Generate contracts:

```bash
python3 scripts/export_openapi.py
python3 scripts/generate_sdk_surfaces.py
```

Check the compiled core:

```bash
cargo test -p multimodal-core
```

Check the TypeScript SDK:

```bash
npm run --prefix sdk/typescript check
```

Generated outputs:

- `openapi/openapi.json`
- `sdk/typescript/src/generated-openapi.ts`
- `sdk/python/src/advanced_multimodal_ai_client/generated_openapi.py`

</details>

<details>
  <summary><strong>Boundaries</strong></summary>

- Public pages summarize generated artifacts; they do not replace the backend.
- Raw media should stay in object storage, public references, or local test fixtures.
- The music lane persists manifests, derived features, embeddings, receipts, and drift reports.
- Research files stay visible but are not described as production infrastructure by default.
- Connector intake is typed and bounded by explicit source rules.
- Stewardship, half-life, supply chain, and residency are treated as runtime review surfaces.

The longer version lives in
[`docs/GROUNDING_AND_BOUNDARIES.md`](./docs/GROUNDING_AND_BOUNDARIES.md).

</details>

<details>
  <summary><strong>Verification commands</strong></summary>

```bash
python3 -m pytest -q
python3 -m ruff check src tests scripts
cargo test -p multimodal-core
npm run --prefix sdk/typescript check
make proof
make acceptance
```

</details>

<details>
  <summary><strong>Research registry</strong></summary>

Some files remain research assets rather than the default runtime path:

- `complete_model.py`
- `dynamic_transformer.py`
- `fusion_strategies.py`
- `core/attention_mechanisms.py`
- `Advanced_/microscopic_signal_pathways.py`

They remain useful as archive and experimentation lanes. The runtime claims in
this README are tied to `src/advanced_multimodal_ai`, generated contracts,
proof exports, tests, and examples.

</details>

<details>
  <summary><strong>License, authorship, and acknowledgment</strong></summary>

This repository is licensed under the Apache License 2.0. See
[`LICENSE`](./LICENSE) and [`NOTICE`](./NOTICE).

The runtime spine, public documentation, and multimodal data-plane contracts in
this refactor are attributed to Cazandra Aporbo.

The transcript-first video lane was informed in part by the structured editing
posture demonstrated in
[browser-use/video-use](https://github.com/browser-use/video-use), especially
its preference for readable timeline packets over indiscriminate frame dumping.
This repository adapts that idea into a narrower multimodal evidence and
cleanup surface rather than copying its editing workflow.

</details>
