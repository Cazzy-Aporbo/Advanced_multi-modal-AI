# Advanced Multi-modal AI

A multimodal systems repository for people who need to see how
different signals are gathered, cleaned, aligned, and carried forward without
losing the evidence along the way.

This repository now holds two things in a clearer arrangement:

- a research archive of models and experiments already present in the project,
- a working runtime edge with typed contracts, retrieval, temporal alignment,
  provenance receipts, and transcript-first video tooling.

[Signal Atlas](https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/Advanced_multi-modal-AI/blob/main/index.html)  
[Architecture Surface](https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/Advanced_multi-modal-AI/blob/main/advanced-technical-portfolio.html)  
[Component Catalog](https://htmlpreview.github.io/?https://github.com/Cazzy-Aporbo/Advanced_multi-modal-AI/blob/main/technical-portfolio.html)

## Table of contents

- [What this repository is](#what-this-repository-is)
- [What runs today](#what-runs-today)
- [The multimodal data plane](#the-multimodal-data-plane)
- [Dataset contracts and evolution](#dataset-contracts-and-evolution)
- [Connector-fed ingestion](#connector-fed-ingestion)
- [Runtime surfaces](#runtime-surfaces)
- [Repository layout](#repository-layout)
- [Quick start](#quick-start)
- [Rust core and TypeScript SDK](#rust-core-and-typescript-sdk)
- [Research registry](#research-registry)
- [Verification](#verification)
- [License and authorship](#license-and-authorship)
- [Acknowledgment](#acknowledgment)

## What this repository is

It is a polyglot repository with a practical runtime spine:

- Python for the service edge, contract validation, orchestration, and
  integration logic
- Rust for deterministic signal primitives that benefit from a compiled lane
- TypeScript for a small client SDK that downstream applications can use

The larger aim is straightforward. Keep the research visible, keep the runtime
clear, and make the interfaces small enough to verify.

## What runs today

The runtime under [`src/advanced_multimodal_ai`](./src/advanced_multimodal_ai)
is operational today.

- FastAPI application with health, readiness, registry, planning, inference,
  retrieval, video, data quality, provenance, alignment, and metrics surfaces
- deterministic contract-mode inference for multimodal tensor payloads
- optional research-mode bridge to existing PyTorch assets already in the repo
- in-memory vector retrieval with stricter dimensional validation
- optional Qdrant retrieval backend
- transcript-first video packeting and cleanup planning
- data quality profiling for modality sparsity, entropy, finite-value coverage,
  and fusion readiness
- dataset contract registration, deterministic schema fingerprinting, and
  schema evolution checks
- typed dataset connectors for local CSV, local Parquet, S3-hosted Parquet,
  local NDJSON, HTTP JSON, HTTP NDJSON, and public HTML pages with robots-aware
  intake rules
- benchmarked connector runs with persisted records
- compiled recipe manifests with persisted launch topology and export checks
- runtime attestation and readiness reporting tied to the generated artifacts
- deterministic provenance receipts for repeated payload verification
- temporal alignment windows for cross-modal evidence stitching
- persisted drift baselines and population-entry checks before reuse
- pipeline ingestion with persisted run records and modality pairing discipline
- domain ontology ingestion for contracts, schemas, and workflow artifacts
- liability surfacing against saved governance snapshots and live trace records
- a sixty-category bias taxonomy with stage-aware assessment
- persisted async job records for long-running video cleanup and batch inference
- Prometheus metrics
- a Rust algorithm core for tensor signatures and transcript-led cut logic
- OpenAPI export and generated Python and TypeScript client surfaces
- a TypeScript SDK for browser and application integration
- Docker, Compose, CI, and GitHub Pages assets that match the actual project

## The multimodal data plane

The real value of a multimodal system is not only inference. It is the care
that happens before and around inference.

## Dataset contracts and evolution

`POST /v1/catalog/register`  
`GET /v1/catalog/datasets`  
`GET /v1/catalog/datasets/{dataset_id}`  
`POST /v1/catalog/evolution`

The runtime now has a persisted catalog lane for datasets as well.

- each dataset contract stores owner, version, modality, primary keys,
  partition keys, and field-level schema
- schema fingerprints are deterministic and can use the Rust core when it is
  available
- candidate revisions can be compared against the latest saved contract to
  separate additive changes from breaking ones

This is a real backend surface and a better starting point for ingestion
governance than a spreadsheet of column names.

## Connector-fed ingestion

`POST /v1/connectors/register`  
`POST /v1/connectors/pipeline-ingest`  
`GET /v1/connectors/runs`  
`GET /v1/connectors/runs/{run_id}`

The runtime can now materialize rows from typed connectors instead of asking
every caller to prepare tensors by hand first.

Supported connector kinds today:

- `local_csv`
- `local_jsonl`
- `local_parquet`
- `s3_parquet`
- `http_json`
- `http_ndjson`
- `web_html`

Each connector run records:

- fetch time
- parse time
- total time
- bytes read
- rows per second

The registration lane infers a dataset contract from real rows and persists
that contract into the catalog. The pipeline-ingest lane goes further: it maps
selected numeric fields into modality tensors, builds pipeline events, and
writes a persisted pipeline run that can later be exported or replayed.

Parquet is now part of the same proof path, including an S3-shaped object-store
lane, so a columnar batch extract can be registered and ingested without first
being flattened into CSV.

The web lane adds a more careful intake path for public pages:

- domain allowlists can be declared before a fetch begins
- `robots.txt` can be checked before any page body is read
- minimum request intervals are enforced per domain when a recent fetch receipt
  is already on record
- byte caps prevent oversized page pulls from becoming the default path
- extracted rows keep text blocks, counts, and page-level receipts together

That keeps web intake useful for research and review work without turning the
repository into an indiscriminate crawler.

## Recipe registry

`POST /v1/recipes/compile`  
`GET /v1/recipes`  
`GET /v1/recipes/{recipe_id}`

The runtime can now compile a typed recipe manifest that:

- resolves dataset references against the persisted catalog
- estimates batch topology from node, device, and accumulation settings
- records verified export and manifest-validation commands
- leaves a persisted handoff record instead of a loose training note

This lane is deliberately careful. It proves the handoff surface, the evidence
resolution, and the manifest discipline before an external runner takes over.

### 1. Quality profiling

`POST /v1/data/profile`

This surface inspects each modality before fusion:

- batch size and feature width
- finite-value coverage
- zero-density and sparsity pressure
- normalized entropy
- signal energy
- dynamic range
- temporal change across the current window
- pairwise signature alignment between modalities

The response includes a fusion-readiness score and explicit warnings when a lane
is too flat, too sparse, or too unstable to carry much weight.

### 2. Provenance receipts

`POST /v1/data/provenance`

This surface produces deterministic SHA-256 receipts for:

- each modality payload
- request metadata
- the full request body

Identical payloads produce identical receipts. Small upstream changes remain
visible because the metadata and modality tensors are hashed separately.

### 3. Temporal alignment

`POST /v1/alignment/windows`

This surface groups timed observations into aligned windows so text, audio,
image, video, or sensor events can be read together instead of as isolated
moments. It is meant for corroboration, not spectacle.

### 4. Retrieval with cleaner boundaries

`POST /v1/retrieval/upsert`  
`POST /v1/retrieval/query`

The retrieval lane now enforces vector width consistency per modality in the
in-memory index. The Qdrant path uses a deterministic point identifier instead
of ephemeral numeric inserts, which makes repeated writes less fragile.

### 5. Video as a temporal modality

`POST /v1/video/packet`  
`POST /v1/video/clean`

The video lane reads transcript timing first, then folds frame and audio
signals into the places where they are actually useful:

- evidence windows
- filler detection
- silence-gap detection
- retained spans
- cut-script preparation

That keeps the surface modest and still useful for review, retrieval, and edit
handoff.

### 6. Long-running work without a theatrical queue

`POST /v1/jobs/video-clean`  
`POST /v1/jobs/batch-infer`  
`GET /v1/jobs`  
`GET /v1/jobs/{job_id}`

The job lane is backed by a persisted SQLite record under `.runtime/`.

- video cleanup can run as an asynchronous job
- multimodal batch inference can run as an asynchronous job
- queued, running, completed, and failed states are stored
- request payloads and result payloads remain inspectable after completion

### 7. Population-entry drift control

`POST /v1/drift/baselines`  
`GET /v1/drift/baselines`  
`POST /v1/drift/check`

The runtime can now save a reviewed population baseline and compare new traffic
against it before that traffic is folded into a familiar lane.

- modality-level entropy, sparsity, finite coverage, range, and temporal motion
  are compared against the saved baseline
- cross-modal alignment drop is measured explicitly
- the runtime can warn or block when a new population drifts outside the
  prepared lane

### 8. Pipeline ingestion with persisted run records

`POST /v1/pipelines/ingest`  
`GET /v1/pipelines/runs`  
`GET /v1/pipelines/runs/{run_id}`  
`GET /v1/pipelines/runs/{run_id}/export`  
`POST /v1/pipelines/runs/{run_id}/replay`

This lane turns raw multimodal events into a paired inference batch, records
what was dropped to preserve alignment, and saves the full run with provenance,
quality, optional drift findings, and inference output.

The export and replay surfaces add a practical audit path:

- rerun the stored request snapshot through the current runtime
- compare provenance and summary shape stability
- export event lineage as NDJSON with deterministic artifact digests

### 9. Domain ontology and liability surfacing

`POST /v1/ontology/ingest`  
`GET /v1/ontology/snapshots`  
`GET /v1/ontology/snapshots/{snapshot_id}`  
`POST /v1/ontology/liability`

This lane ingests API schemas, workflow notes, and governance artifacts into a
persisted ontology snapshot. The liability surface then compares live route
traces against compiled constraints such as encryption requirements,
cross-border transfer boundaries, and reviewed handling lanes.

### 10. Bias as a staged system problem

`GET /v1/bias/taxonomy`  
`POST /v1/bias/assess`

The repository now carries a sixty-category bias taxonomy across collection,
consent, sampling, measurement, labeling, feature shaping, retrieval,
evaluation, interface, and governance. The assessment lane reports where risk
is entering the system rather than compressing bias into one generic score.

### 11. Runtime attestation

`GET /v1/runtime/attestation`
`GET /v1/readiness/report`

This surface returns an evidence bundle about what the repo can verify today:
OpenAPI digest, generated client artifacts, runtime schema, Rust core
presence, and persisted record counts across the local stores.

The readiness report stays adjacent to that attestation. It assembles route
count, test count, connector coverage, resolved recipe evidence, and operating
boundaries into one typed response so the repo can state what is review-ready,
what still needs evidence, and where the runtime is intentionally restrained.

## Runtime surfaces

| Surface | Method | Purpose |
| --- | --- | --- |
| `/v1/health` | `GET` | service health, environment, and metrics posture |
| `/v1/ready` | `GET` | runtime readiness, model count, and retrieval backend |
| `/v1/catalog/register` | `POST` | save a versioned dataset contract |
| `/v1/catalog/datasets` | `GET` | list persisted dataset contracts |
| `/v1/catalog/datasets/{dataset_id}` | `GET` | read one persisted dataset contract |
| `/v1/catalog/evolution` | `POST` | compare a candidate schema against the latest saved version |
| `/v1/connectors/register` | `POST` | infer and persist a dataset contract from file, object-store, HTTP, or public-web rows |
| `/v1/connectors/pipeline-ingest` | `POST` | fetch rows, map features into modalities, and persist a pipeline run |
| `/v1/connectors/runs` | `GET` | list benchmarked connector runs |
| `/v1/connectors/runs/{run_id}` | `GET` | read one persisted connector run |
| `/v1/recipes/compile` | `POST` | compile a typed recipe manifest with launch topology and proof obligations |
| `/v1/recipes` | `GET` | list persisted recipe manifests |
| `/v1/recipes/{recipe_id}` | `GET` | read one persisted recipe manifest |
| `/v1/runtime/attestation` | `GET` | present-tense evidence of generated artifacts and persisted stores |
| `/v1/proof/bundle` | `GET` | summarize routes, tests, verification commands, connectors, artifacts, and store counts |
| `/v1/readiness/report` | `GET` | assemble evidence checks, connector coverage, recipe resolution, and operating boundaries |
| `/v1/models` | `GET` | registered runtime and research model inventory |
| `/v1/bias/taxonomy` | `GET` | sixty-category bias register across the system lifecycle |
| `/v1/bias/assess` | `POST` | stage-aware bias findings for an active system |
| `/v1/plan` | `POST` | orchestration steps before execution |
| `/v1/data/profile` | `POST` | modality quality, pairwise alignment, and fusion readiness |
| `/v1/data/provenance` | `POST` | deterministic request receipts |
| `/v1/drift/baselines` | `POST` | save a reviewed population baseline |
| `/v1/drift/baselines` | `GET` | list saved drift baselines |
| `/v1/drift/check` | `POST` | compare a new population to a reviewed baseline |
| `/v1/pipelines/ingest` | `POST` | ingest multimodal events into a persisted pipeline run |
| `/v1/pipelines/runs` | `GET` | list persisted pipeline runs |
| `/v1/pipelines/runs/{run_id}` | `GET` | read one persisted pipeline run |
| `/v1/pipelines/runs/{run_id}/export` | `GET` | export event lineage and artifact digests for one run |
| `/v1/pipelines/runs/{run_id}/replay` | `POST` | rerun a saved request snapshot through the current runtime |
| `/v1/ontology/ingest` | `POST` | compile enterprise artifacts into an ontology snapshot |
| `/v1/ontology/snapshots` | `GET` | list persisted ontology snapshots |
| `/v1/ontology/snapshots/{snapshot_id}` | `GET` | read one ontology snapshot |
| `/v1/ontology/liability` | `POST` | compare live traces against compiled governance constraints |
| `/v1/infer` | `POST` | contract-mode or research-mode multimodal inference |
| `/v1/stream` | `WebSocket` | accepted → plan → progress → result stream |
| `/v1/alignment/windows` | `POST` | temporal grouping across modalities |
| `/v1/jobs/video-clean` | `POST` | enqueue a persisted video cleanup job |
| `/v1/jobs/batch-infer` | `POST` | enqueue a persisted batch inference job |
| `/v1/jobs` | `GET` | list persisted run records |
| `/v1/jobs/{job_id}` | `GET` | read one persisted run record |
| `/v1/retrieval/upsert` | `POST` | vector write into the active retrieval backend |
| `/v1/retrieval/query` | `POST` | nearest-neighbor multimodal context read |
| `/v1/video/packet` | `POST` | transcript-led evidence window assembly |
| `/v1/video/clean` | `POST` | cleanup suggestions for filler and silence |
| `/v1/benchmarks/smoke` | `GET` | deterministic smoke benchmark |
| `/metrics` | `GET` | Prometheus scrape target |

## Repository layout

```text
Advanced_multi-modal-AI/
├── crates/multimodal-core/       # Rust signal core for signatures and temporal cuts
├── sdk/typescript/               # TypeScript client SDK
├── src/advanced_multimodal_ai/
│   ├── alignment.py              # timed observation grouping across modalities
│   ├── api.py                    # FastAPI entrypoint
│   ├── attestation.py            # runtime evidence and artifact verification
│   ├── bias_taxonomy.py          # sixty-category bias register and assessment
│   ├── catalog.py                # dataset contract registration and evolution logic
│   ├── catalog_store.py          # persisted dataset catalog records
│   ├── benchmarks.py             # deterministic smoke benchmark
│   ├── cli.py                    # local serve and benchmark commands
│   ├── config.py                 # environment-backed settings
│   ├── connector_store.py        # persisted connector benchmark records
│   ├── connectors.py             # typed connector pulls, web intake policy checks, and row mapping
│   ├── contracts.py              # API, runtime, quality, and provenance schemas
│   ├── domain_ontology.py        # artifact ingestion and contract compilation
│   ├── drift.py                  # population-entry drift scoring
│   ├── drift_store.py            # persisted baseline registry
│   ├── job_store.py              # SQLite-backed persisted async run records
│   ├── legacy.py                 # bridge to existing research models
│   ├── liability_surface.py      # route trace comparison against constraints
│   ├── observability.py          # Prometheus counters and histograms
│   ├── ontology_store.py         # persisted ontology snapshots
│   ├── orchestration.py          # runtime planning steps
│   ├── pipeline_store.py         # persisted multimodal pipeline runs
│   ├── pipelines.py              # raw event pairing into inference batches
│   ├── provenance.py             # deterministic receipt generation
│   ├── quality.py                # modality quality and fusion readiness
│   ├── recipe_store.py           # persisted recipe manifests
│   ├── recipes.py                # recipe compilation and launch shaping
│   ├── replay.py                 # pipeline export and replay comparison
│   ├── registry.py               # model inventory surface
│   ├── retrieval.py              # vector index implementations
│   ├── rust_bridge.py            # optional bridge into the Rust core
│   ├── service.py                # inference and coordination logic
│   ├── signal_math.py            # shared tensor summaries and signature math
│   └── video.py                  # transcript-first video packet and cleanup lane
├── tests/                        # API, retrieval, and video verification
├── monitoring/prometheus.yml     # scrape configuration
├── examples/README.md            # direct runbook for executable examples
├── sql/runtime_schema.sql        # persisted runtime tables
├── prompts/elite_engineer_transformation_v3.md
├── proof/example-bundle.json
├── proof/example-bundle.md
├── proof/runtime-proof.json
├── proof/runtime-proof.md
├── Dockerfile
├── compose.yaml
├── openapi/openapi.json
├── scripts/build_runtime_proof_bundle.py
├── scripts/export_example_bundle.py
├── scripts/export_openapi.py
├── scripts/generate_sdk_surfaces.py
├── scripts/run_acceptance_spine.py
├── complete_model.py
├── dynamic_transformer.py
├── fusion_strategies.py
└── core/attention_mechanisms.py
```

## Quick start

### 1. Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
```

### 2. Run the API

```bash
uvicorn advanced_multimodal_ai.api:create_app --factory --host 0.0.0.0 --port 8000
```

Open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/v1/health`
- `http://127.0.0.1:8000/metrics`

### 3. Run tests

```bash
pytest
ruff check src tests
cargo test -p multimodal-core
python3 scripts/run_acceptance_spine.py
```

### 4. Run the benchmark

```bash
python -m advanced_multimodal_ai.cli benchmark --iterations 10
```

### 5. Export the example bundle

```bash
python3 scripts/export_example_bundle.py
```

That writes:

- `proof/example-bundle.json`
- `proof/example-bundle.md`

### 6. Run the acceptance spine

```bash
python3 scripts/run_acceptance_spine.py
```

### 7. Start the full local stack

```bash
docker compose up --build
```

This brings up:

- the FastAPI service
- Qdrant
- Prometheus

## Rust core and TypeScript SDK

### Rust core

```bash
cargo test -p multimodal-core
```

The Rust crate handles two deterministic surfaces today:

- tensor signature extraction for contract-mode inference
- transcript-led cleanup cut detection for the video lane

### TypeScript SDK

The client under [`sdk/typescript`](./sdk/typescript) covers:

- health checks
- model registry reads
- data quality profiling
- provenance receipts
- alignment windows
- connector-backed dataset registration
- connector-fed pipeline ingestion
- persisted job submission and job inspection
- inference requests
- orchestration planning
- WebSocket inference streaming

Build check:

```bash
cd sdk/typescript
npx tsc --noEmit -p tsconfig.json
```

### OpenAPI export and generated clients

```bash
python3 scripts/export_openapi.py
python3 scripts/generate_sdk_surfaces.py
python3 scripts/export_readiness_report.py
python3 scripts/export_example_bundle.py
python3 scripts/build_runtime_proof_bundle.py
```

Generated outputs:

- `openapi/openapi.json`
- `sdk/typescript/src/generated-openapi.ts`
- `sdk/python/src/advanced_multimodal_ai_client/generated_openapi.py`
- `proof/readiness-report.json`
- `proof/example-bundle.json`

## Research registry

Some parts of the repository remain research assets rather than finished runtime
components.

- `complete_model.py`
- `dynamic_transformer.py`
- `fusion_strategies.py`
- `core/attention_mechanisms.py`
- several `Advanced_/` experiments

Those files are still useful. They are simply no longer described as though
they were already a distributed production engine on their own.

## Verification

This pass was validated locally with:

- `python3 -m pytest -q`
- `python3 -m ruff check src tests scripts`
- `cargo test -p multimodal-core`
- `python3 scripts/export_openapi.py`
- `python3 scripts/generate_sdk_surfaces.py`
- `python3 scripts/export_readiness_report.py`
- `python3 scripts/export_example_bundle.py`
- `python3 scripts/build_runtime_proof_bundle.py`
- `python3 scripts/run_acceptance_spine.py`
- `npx tsc --noEmit -p sdk/typescript/tsconfig.json`

## License and authorship

This repository is licensed under the Apache License 2.0. See
[`LICENSE`](./LICENSE) and [`NOTICE`](./NOTICE).

The runtime spine, public documentation, and multimodal data-plane contracts in
this refactor are attributed to Cazandra Aporbo.

## Acknowledgment

The transcript-first video lane was informed in part by the structured editing
posture demonstrated in [browser-use/video-use](https://github.com/browser-use/video-use),
especially its preference for readable timeline packets over indiscriminate
frame dumping. This repository adapts that idea into a narrower multimodal
evidence and cleanup surface rather than copying its editing workflow.
