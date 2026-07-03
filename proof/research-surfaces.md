# Research Surfaces

- Service: `advanced-multimodal-ai`
- Version: `0.5.0`
- Readiness posture: `needs_buildout`
- Route count: `69`
- Test count: `46`
- Connector kinds: `7`
- Models: `4`
- Runtime-ready models: `0`
- Open questions: `5`

## Architecture lanes

### Atlas and public study surfaces

- Lane id: `atlas_frontend`
- Layer: `frontend`

Translate runtime proof, model notes, and research findings into readable public pages without moving inference into the browser.

Why it exists:
The public pages should stay legible and alive while remaining downstream from the backend source of truth.

Directories:
- `index.html`
- `advanced-technical-portfolio.html`
- `technical-portfolio.html`
- `model-observatory.html`
- `field-notes.html`
- `benchmark-observatory.html`
- `cymatic-media-engine.html`
- `cymatic-surface.css`
- `cymatic-surface.js`
- `research-surfaces.js`

Entry surfaces:
- `proof/research-surfaces.json`
- `proof/runtime-proof.json`
- `proof/readiness-report.json`
- `proof/benchmark-surfaces.json`
- `proof/cymatic-surface.json`

Outputs:
- Signal Atlas
- Architecture Surface
- Component Catalog
- Model Observatory
- Field Notes
- Benchmark Observatory
- Cymatic Media Engine

Proof points:
- Generated proof exports are read directly by the browser lane.
- The atlas remains a display surface rather than a silent compute fork.


### Runtime API and orchestration spine

- Lane id: `runtime_backend`
- Layer: `backend`

Hold the typed contracts, ingestion, inference, replay, retrieval, drift, stewardship, and job surfaces in one tested service edge.

Why it exists:
This is the working service lane. It carries operational state, review state, and exported evidence together.

Directories:
- `src/advanced_multimodal_ai/api.py`
- `src/advanced_multimodal_ai/service.py`
- `src/advanced_multimodal_ai/connectors.py`
- `src/advanced_multimodal_ai/pipelines.py`
- `src/advanced_multimodal_ai/stewardship_store.py`
- `src/advanced_multimodal_ai/benchmarks.py`

Entry surfaces:
- `/v1/infer`
- `/v1/connectors/pipeline-ingest`
- `/v1/pipelines/ingest`
- `/v1/research/surfaces`
- `/v1/benchmarks/reference`

Outputs:
- Typed API responses
- Persisted run records
- Connector benchmarks
- Research surface bundle
- Reference workload benchmark

Proof points:
- pytest covers API behavior directly through FastAPI TestClient.
- Runtime attestation and proof bundle are emitted from the same backend package.


### Compiled signal core

- Lane id: `compiled_core`
- Layer: `compiled`

Keep deterministic tensor signatures and transcript-led cut logic in a compiled lane that can be tested separately.

Why it exists:
Compiled primitives stay small and explicit so performance work does not blur into orchestration code.

Directories:
- `crates/multimodal-core`
- `src/advanced_multimodal_ai/rust_bridge.py`

Entry surfaces:
- `cargo test -p multimodal-core`
- `/v1/data/provenance`
- `/v1/video/cuts`

Outputs:
- Deterministic signatures
- Video cut proposals

Proof points:
- Cargo tests validate the compiled lane independently.
- Python runtime surfaces call through a narrow bridge rather than reimplementing the logic.


### Benchmark evidence lane

- Lane id: `benchmark_evidence`
- Layer: `evidence`

Exercise connector ingest, profiling, provenance, batch work, recipe handoff, and proof export together through one repeatable workload.

Why it exists:
A benchmark becomes more persuasive when it proves the choreography between lanes, not only isolated speed.

Directories:
- `src/advanced_multimodal_ai/benchmarks.py`
- `scripts/export_benchmark_surfaces.py`
- `proof/benchmark-surfaces.json`
- `proof/benchmark-surfaces.md`

Entry surfaces:
- `/v1/benchmarks/reference`
- `python3 scripts/export_benchmark_surfaces.py`

Outputs:
- reference benchmark JSON
- reference benchmark Markdown

Proof points:
- The benchmark walks real repository lanes rather than timing an isolated helper.
- The public site can hydrate directly from generated benchmark evidence.


### Generated client surfaces

- Lane id: `generated_clients`
- Layer: `client`

Freeze the public API contract into reusable Python and TypeScript clients instead of asking downstream users to hand-copy payload shapes.

Why it exists:
Client packaging belongs beside the contract it reflects, not in a separate storytelling lane.

Directories:
- `openapi/openapi.json`
- `sdk/python`
- `sdk/typescript`
- `scripts/export_openapi.py`
- `scripts/generate_sdk_surfaces.py`

Entry surfaces:
- `python3 scripts/export_openapi.py`
- `python3 scripts/generate_sdk_surfaces.py`
- `npm run --prefix sdk/typescript check`

Outputs:
- Python client
- TypeScript client
- OpenAPI contract

Proof points:
- Generated clients are rebuilt from the live app contract.
- TypeScript compilation confirms the generated surface remains coherent.


### Proof and replay archive

- Lane id: `proof_exports`
- Layer: `evidence`

Publish runtime proof, readiness posture, worked examples, and research surfaces as exportable artifacts.

Why it exists:
A repository becomes easier to trust when proof can be regenerated, inspected, and linked back to running code.

Directories:
- `proof`
- `scripts/build_runtime_proof_bundle.py`
- `scripts/export_execution_journal.py`
- `scripts/export_readiness_report.py`
- `scripts/export_example_bundle.py`
- `scripts/export_research_surfaces.py`

Entry surfaces:
- `/v1/runtime/attestation`
- `/v1/proof/bundle`
- `/v1/readiness/report`
- `/v1/research/surfaces`
- `/v1/execution/journal`

Outputs:
- runtime-proof.json
- readiness-report.json
- example-bundle.json
- research-surfaces.json
- execution-journal.json

Proof points:
- Exports can be regenerated locally from the runtime.
- The static site reads the same evidence files that verification emits.
- Export and verification scripts now write their own journal receipts.


## Model cards

### Adaptive Multimodal Transformer

- Model id: `adaptive_transformer`
- Source file: `dynamic_transformer.py`
- Runtime ready: `False`
- Supports contract mode: `True`
- Supports research mode: `True`
- Evidence surfaces: /v1/infer, /v1/stream, /v1/data/profile, /v1/drift/check
- Related files: dynamic_transformer.py, src/advanced_multimodal_ai/service.py, src/advanced_multimodal_ai/quality.py, src/advanced_multimodal_ai/drift.py

The main bridge between the contract-safe tensor edge and the broader research archive.

Why this model lives here:
It gives the repository one serious multimodal model that can be discussed in terms of routing, fusion discipline, and uncertainty without requiring the public runtime to pretend every research branch is production-ready.

Strengths:
- Handles uneven modality mixtures without requiring every lane to be equally rich.
- Keeps hierarchical fusion visible enough to study where signal loss begins.
- Supports contract-mode summaries beside research-mode exploration.

Limits:
- Still needs broader paired data before its behavior on long video-heavy work is persuasive.
- Runtime evidence is stronger on tensor orchestration than on full-scale training outcomes.
- Calibration remains modest unless uncertainty output is explicitly exercised.

Improvement paths:
- Add evaluated transcript-plus-frame corpora with stronger long-range temporal supervision.
- Track calibration error and abstention behavior as first-class benchmark outputs.
- Compare its fusion posture against narrower baselines under population-entry drift.

Open questions:
- **When does hierarchical fusion help more than it hides weak modality evidence?**
  - Why it matters: A multimodal model can appear impressive while quietly leaning too hard on the easiest modality in the room.
  - Current position: The repository now measures entropy, sparsity, and alignment before fusion, but it still needs richer comparative evaluation sets.
- **What should count as enough uncertainty to hold a result back?**
  - Why it matters: Confidence without a stopping rule is not especially helpful in a live system.
  - Current position: Uncertainty can be surfaced, though the evidence story is stronger than the current threshold policy.


### Complete Multimodal AI

- Model id: `complete_multimodal`
- Source file: `complete_model.py`
- Runtime ready: `False`
- Supports contract mode: `True`
- Supports research mode: `True`
- Evidence surfaces: /v1/models, /v1/recipes/compile, /v1/catalog/register, /v1/runtime/attestation
- Related files: complete_model.py, src/advanced_multimodal_ai/recipes.py, src/advanced_multimodal_ai/catalog.py, src/advanced_multimodal_ai/attestation.py

A larger research archive model that shows the full ambition of the repository, including memory and training-oriented helpers.

Why this model lives here:
It preserves the broader design vocabulary of the project without forcing the public runtime to overstate what it can execute every day.

Strengths:
- Shows how modality-specific encoders, routing, and memory can be studied together.
- Makes the repository useful as a learning surface for end-to-end multimodal design.
- Keeps the research ambition visible even when the runtime edge stays narrow.

Limits:
- Too broad to treat as the default live edge without much stronger field evidence.
- Training helpers are present, though the repo is still better at runtime proof than large-scale training proof.
- Needs more dataset-specific evaluation before its claims should travel very far.

Improvement paths:
- Attach explicit benchmark suites for memory-heavy multimodal tasks.
- Document which subsystems are stable enough to graduate into the core runtime.
- Add stronger supply-path evidence for large batch training data movement.

Open questions:
- **Which parts of the larger research model deserve promotion into the runtime edge?**
  - Why it matters: A generous archive is useful, but only if the repo is honest about which pieces have earned operational trust.
  - Current position: The bridge exists. The next step is clearer promotion criteria tied to proof and replay.


### Fusion Strategy Lab

- Model id: `fusion_lab`
- Source file: `fusion_strategies.py`
- Runtime ready: `False`
- Supports contract mode: `True`
- Supports research mode: `False`
- Evidence surfaces: /v1/data/profile, /v1/pipelines/runs/{run_id}/replay
- Related files: fusion_strategies.py, src/advanced_multimodal_ai/quality.py, src/advanced_multimodal_ai/replay.py

A comparative lane for studying how modalities are combined rather than assuming one fusion style suits every problem.

Why this model lives here:
Fusion is usually where multimodal work becomes vague. Keeping it modular makes the tradeoffs easier to inspect and harder to romanticize.

Strengths:
- Lets the repository compare concatenation, gated fusion, bilinear pooling, and hierarchical mixing.
- Supports learning and ablation work without disturbing the public API edge.
- Makes it easier to reason about model behavior in terms of mechanism rather than branding.

Limits:
- It is a lab lane, not a standalone evaluated system.
- It needs more paired benchmarks to show when one fusion path clearly outperforms another.

Improvement paths:
- Attach benchmark matrices showing where each fusion path fails or overfits.
- Bring replay evidence and drift posture into fusion comparisons, not only top-line outputs.

Open questions:
- **How much fusion complexity is actually helpful before it starts hiding fragile evidence?**
  - Why it matters: More machinery can look clever while making failure harder to see.
  - Current position: The repository is better at exposing the options than at ranking them under shared benchmarks.


### Attention Core

- Model id: `attention_core`
- Source file: `core/attention_mechanisms.py`
- Runtime ready: `False`
- Supports contract mode: `True`
- Supports research mode: `False`
- Evidence surfaces: /v1/models, /v1/proof/bundle
- Related files: core/attention_mechanisms.py, dynamic_transformer.py, complete_model.py

A lower-level mechanism lane for cross-modal and sparse attention experiments.

Why this model lives here:
Attention primitives matter here because the project is interested in where cross-modal context is genuinely useful and where it merely makes the system harder to explain.

Strengths:
- Keeps attention work inspectable instead of burying it inside a single large model file.
- Supports experimentation with sparse and cross-modal routing ideas.

Limits:
- It is a mechanism library rather than a measured endpoint on its own.
- Without richer task-level evaluation, it teaches architecture more than it proves performance.

Improvement paths:
- Connect attention experiments to benchmark deltas instead of architectural description alone.
- Add clearer ablation outputs showing what each attention change bought or cost.

Open questions:
- **Which attention variations survive contact with noisy multimodal data?**
  - Why it matters: Elegant attention code can still collapse once the modalities stop cooperating.
  - Current position: The repository names the mechanisms clearly. It still needs more field-shaped comparisons.


## Findings

### The repository now begins with measured intake instead of hand-shaped payloads alone

- Lens: `data`
- Finding id: `connector-spine-is-real`
- Related surfaces: /v1/connectors/register, /v1/connectors/pipeline-ingest, /v1/catalog/register
- Related files: src/advanced_multimodal_ai/connectors.py, src/advanced_multimodal_ai/catalog.py, src/advanced_multimodal_ai/pipelines.py

291 connector runs and 7 typed connector kinds mean the repo can start from rows, contracts, and public pages before tensor work begins.

Evidence:
- connector runs recorded: 291
- connector kinds exported: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html

Why it matters:
A multimodal repository becomes more credible when data entry is a first-class engineering problem rather than an invisible notebook precondition.

Next step:
Broaden the evidence base with more repeated connector runs against non-trivial sources so the intake lane is tested under variation, not only under design-time examples.


### Review work now sits beside inference instead of after it

- Lens: `governance`
- Finding id: `review-lives-next-to-runtime`
- Related surfaces: /v1/stewardship/posture, /v1/drift/check, /v1/ontology/liability
- Related files: src/advanced_multimodal_ai/stewardship_store.py, src/advanced_multimodal_ai/drift.py, src/advanced_multimodal_ai/liability_surface.py

Lifecycle policies (21), change controls (21), supply snapshots (21), drift baselines (8), and ontology snapshots (102) are persisted in the same backend story.

Evidence:
- lifecycle policies: 21
- change controls: 21
- supply snapshots: 21
- drift baselines: 8
- ontology snapshots: 102

Why it matters:
It is easier to trust a system when retention, movement, and liability have a code path rather than only a meeting note.

Next step:
Keep tying review surfaces to real route traces so the governance lane reflects operational movement, not just intended policy.


### The research archive remains visible without pretending it is the whole runtime

- Lens: `research`
- Finding id: `archive-and-runtime-are-distinct`
- Related surfaces: /v1/models, /v1/research/models
- Related files: src/advanced_multimodal_ai/registry.py, src/advanced_multimodal_ai/research_surfaces.py, dynamic_transformer.py, complete_model.py

0 of 4 listed models are runtime-ready in the current environment. That separation makes the repo more honest about what is live today and what still belongs to active study.

Evidence:
- listed models: 4
- runtime-ready models: 0

Why it matters:
A public repository becomes easier to adopt when it is clear which layers are operational, which are archival, and how the two still inform each other.

Next step:
Add stronger benchmark evidence for the research archive so promotion into the runtime edge can be argued from results rather than enthusiasm.


### Proof is no longer only a README habit

- Lens: `evaluation`
- Finding id: `proof-is-now-a-backend-surface`
- Related surfaces: /v1/proof/bundle, /v1/runtime/attestation, /v1/readiness/report
- Related files: src/advanced_multimodal_ai/proof.py, src/advanced_multimodal_ai/attestation.py, scripts/export_readiness_report.py

The bundle currently counts 69 routes, 46 tests, and 9 declared artifacts.

Evidence:
- route count: 69
- test count: 46
- verification artifacts: 9
- pipeline runs stored: 226

Why it matters:
Trust improves when proof is generated from code paths that actually exist and can be re-exported for the public site.

Next step:
Keep the export surfaces close to CI and extend replay comparisons so proof covers behavioral continuity, not only route and artifact presence.


### Export and verification work now leaves its own operational memory

- Lens: `evaluation`
- Finding id: `execution-memory-is-persisted`
- Related surfaces: /v1/execution/journal, /v1/repository/pulse
- Related files: src/advanced_multimodal_ai/execution_journal.py, src/advanced_multimodal_ai/execution_journal_store.py, scripts/export_execution_journal.py

50 persisted execution-journal runs now describe which proof and packaging lanes actually ran, what they touched, and when they last changed.

Evidence:
- execution journal runs: 50
- proof/execution-journal.json is exported from the backend journal surface.

Why it matters:
A repository feels more trustworthy when its export and verification lanes can be revisited as records instead of being remembered only because someone ran them recently.

Next step:
Keep letting new export and benchmark lanes write their own receipts so operational continuity becomes visible over time.


### The benchmark lane now tests choreography, not just speed

- Lens: `evaluation`
- Finding id: `reference-benchmark-lane-is-repeatable`
- Related surfaces: /v1/benchmarks/reference, /v1/jobs/batch-infer, /v1/connectors/pipeline-ingest
- Related files: src/advanced_multimodal_ai/benchmarks.py, src/advanced_multimodal_ai/service.py, scripts/export_benchmark_surfaces.py

A typed reference workload now exercises connector-backed ingest, profiling, provenance, concurrent batch execution, recipe compilation, and proof export as one repeatable route.

Evidence:
- Reference benchmark surface: /v1/benchmarks/reference
- Generated artifact: proof/benchmark-surfaces.json
- Concurrent job evidence is persisted under the async job store.

Why it matters:
This shifts the repository away from isolated timing theatre and toward proof that multiple lanes can keep their story straight together.

Next step:
Keep widening the benchmark inputs with more warehouse-shaped and public-domain workloads so the same route is tested under broader operational texture.


### The next gains will come from deeper field evidence, not louder claims

- Lens: `runtime`
- Finding id: `what-still-needs-field-time`
- Related surfaces: /v1/readiness/report, /v1/pipelines/runs/{run_id}/replay, /v1/recipes/compile
- Related files: src/advanced_multimodal_ai/readiness.py, src/advanced_multimodal_ai/replay.py, src/advanced_multimodal_ai/recipes.py

The current readiness posture is 'needs_buildout'. The repo now has a steadier runtime edge, though the strongest next step remains more repeated evidence under varied real inputs.

Evidence:
- readiness posture: needs_buildout
- connector runs: 291
- pipeline runs: 226
- compiled recipes: 63

Why it matters:
The repository is more valuable when it is explicit about what has been proven, what is promising, and what still needs to earn its place.

Next step:
Bring in more repeated warehouse, object-store, and mixed-modality examples so the runtime is exercised under broader operational texture.


## Connections

### Rows become batches through typed evidence, not through silent reshaping

- Connection id: `rows-to-batches`

The intake path begins in connectors.py, becomes a dataset contract in catalog.py, and only then moves into pipelines.py where modality batches are assembled.

Files:
- `src/advanced_multimodal_ai/connectors.py`
- `src/advanced_multimodal_ai/catalog.py`
- `src/advanced_multimodal_ai/pipelines.py`

API surfaces:
- `/v1/connectors/register`
- `/v1/connectors/pipeline-ingest`
- `/v1/catalog/register`

Learning value:
It shows how to keep ingestion, schema care, and tensor preparation in one chain without hiding the transformations.

Watch points:
- Too many dropped rows usually means the modality mapping is doing more damage than help.
- A dataset contract should be registered before batch work becomes the default path.


### Measurement sits in front of inference instead of apologizing after it

- Connection id: `measurement-before-fusion`

quality.py, signal_math.py, provenance.py, and alignment.py give the runtime a chance to say what it knows about the data before service.py turns that data into output.

Files:
- `src/advanced_multimodal_ai/quality.py`
- `src/advanced_multimodal_ai/signal_math.py`
- `src/advanced_multimodal_ai/provenance.py`
- `src/advanced_multimodal_ai/alignment.py`
- `src/advanced_multimodal_ai/service.py`

API surfaces:
- `/v1/data/profile`
- `/v1/data/provenance`
- `/v1/alignment/windows`
- `/v1/infer`

Learning value:
This is where the repository becomes useful for people who care how a signal was treated, not only what a model eventually returned.

Watch points:
- High fusion readiness with weak provenance is still a fragile surface.
- Alignment windows are only persuasive when the original timing remains intact.


### Drift, stewardship, and liability remain part of the same backend story

- Connection id: `review-beside-runtime`

drift.py, stewardship_store.py, domain_ontology.py, and liability_surface.py keep review work close to the routes that need it.

Files:
- `src/advanced_multimodal_ai/drift.py`
- `src/advanced_multimodal_ai/stewardship_store.py`
- `src/advanced_multimodal_ai/domain_ontology.py`
- `src/advanced_multimodal_ai/liability_surface.py`

API surfaces:
- `/v1/drift/check`
- `/v1/stewardship/posture`
- `/v1/ontology/ingest`
- `/v1/ontology/liability`

Learning value:
The repo is more credible when data retirement, cross-border movement, and route mismatch can be inspected through code rather than left to policy prose alone.

Watch points:
- A drift baseline without a review rhythm becomes decoration quickly.
- Cross-border edges deserve the same specificity as model inputs do.


### Proof, OpenAPI export, and SDK generation share one source of truth

- Connection id: `proof-to-client`

attestation.py and proof.py describe what is present; export scripts then freeze the public contract into generated Python and TypeScript surfaces.

Files:
- `src/advanced_multimodal_ai/attestation.py`
- `src/advanced_multimodal_ai/proof.py`
- `scripts/export_openapi.py`
- `scripts/generate_sdk_surfaces.py`

API surfaces:
- `/v1/runtime/attestation`
- `/v1/proof/bundle`
- `/v1/readiness/report`

Learning value:
It shows how documentation and client packaging can stay tethered to a live contract instead of becoming separate stories.

Watch points:
- Generated clients should be regenerated when the contract moves, not only before release.
- Proof is more useful when it counts real stores, routes, and artifacts rather than generic claims.


### Connector proof, batch work, and recipe handoff can now be exercised in one repeatable lane

- Connection id: `connector-proof-benchmark`

benchmarks.py and service.py now use the same connector, profiling, job, recipe, and proof surfaces the runtime already exposes, then publish the result as a generated benchmark artifact.

Files:
- `src/advanced_multimodal_ai/benchmarks.py`
- `src/advanced_multimodal_ai/service.py`
- `scripts/export_benchmark_surfaces.py`
- `proof/benchmark-surfaces.json`

API surfaces:
- `/v1/benchmarks/reference`
- `/v1/connectors/pipeline-ingest`
- `/v1/jobs/batch-infer`
- `/v1/recipes/compile`

Learning value:
This connection makes the repository easier to trust because the same operational lanes are exercised together instead of being admired separately.

Watch points:
- Reference workloads should stay deterministic and readable, not drift into decorative microbenchmarks.
- Batch concurrency is useful only when per-item failures stay visible in the stored record.

