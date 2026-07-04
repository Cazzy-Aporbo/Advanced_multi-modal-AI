# Operator Surfaces

## Metrics

- live routes: 100 · The command lattice stays tied to executable contracts.
- test functions: 60 · Proof is carried beside the operator surfaces, not after them.
- named models: 4 · Model count stays visible so command breadth does not drift into theater.
- audio manifests: 74 · Raw media stays external while the manifest and feature lane remain inspectable.
- music feature runs: 74 · Every speech-task card below is backed by the same derived warehouse lane.
- language × genre spread: 1 × 2 · Coverage is counted as declared signal breadth, not treated as decoration.

## Command lattice

- **Seal a dataset contract before it moves** · `POST /v1/catalog/register` · contract edge · Name the dataset, its fields, and its hashes before a downstream lane treats it as normal.
- **Ingest rows through a named connector lane** · `POST /v1/connectors/pipeline-ingest` · connector spine · Move object-store or file-backed evidence into the replayable pipeline without flattening source provenance.
- **Materialize a sound lane without storing the track** · `POST /v1/music/features/extract` · music warehouse · Turn an audio reference into segments, derived features, embeddings, and receipts that can be queried later.
- **Queue long-running multimodal work with receipts** · `POST /v1/jobs/batch-infer` · async execution · Keep batch work observable while preserving a typed request, a run journal, and replayable artifacts.
- **Re-run the same workload through many lanes** · `POST /v1/benchmarks/reference` · benchmark lane · Exercise ingest, replay, batch work, recipe compilation, and proof refresh under one reference workload.
- **Export a readable proof surface from the same runtime** · `GET /v1/operators/surfaces` · proof export · Give the frontend, the SDKs, and the repository pages one typed surface to read when the operator lane changes.
- **Evaluate a multimodal packet before it moves deeper** · `POST /v1/edge/evaluate` · edge gateway · Measure packet geometry, cross-border posture, and encrypted transport before downstream orchestration turns a weak packet into a stronger claim.

## Skill surfaces

- **Schema fingerprinting** · Keep upstream changes from silently mutating downstream assumptions. · related commands: catalog-register
- **Music warehouse segmentation** · Translate one audio reference into stable windows that can survive query, drift review, and cross-modal alignment. · related commands: music-feature-extract
- **Connector replay verification** · Prove that the reconstructed run still matches the sealed frame chain after ingest. · related commands: connector-pipeline-ingest, reference-benchmark
- **Bias and liability reading** · Keep weak-signal drift, representational skew, and liability gaps close to the routes that produced them. · related commands: proof-refresh
- **Generated client discipline** · Keep SDKs downstream from FastAPI contracts so the typed edges stay aligned. · related commands: proof-refresh
- **Inspect, plan, run, and verify loop** · Turn the current backend state into the next bounded improvement pass instead of waiting for a human to remember every loose edge. · related commands: reference-benchmark, proof-refresh, batch-infer
- **Packet geometry gate** · Use entropy, finite-value coverage, and zero-heavy ratios to slow a packet down before orchestration tries to make more of it. · related commands: edge-evaluate

## Plugin seams

- **Python client seam** · generated client · `sdk/python/src/advanced_multimodal_ai_client/generated_openapi.py`
- **TypeScript client seam** · generated client · `sdk/typescript/src/generated-openapi.ts`
- **Compiled core bridge** · ffi lane · `src/advanced_multimodal_ai/rust_bridge.py`
- **Proof export spine** · export lane · `scripts/run_acceptance_spine.py`
- **Recursive improvement seam** · task loop · `src/advanced_multimodal_ai/service.py`
- **Deployment stack seam** · local stack · `containers/compose.yaml`

## Speech task lattice

- **Speech presence audit** · Separate spoken intervals from music-first or ambience-first windows without storing the waveform in git. · signals: silence ratio, onset density, mfcc summary, transcript refs
- **Language share watch** · Keep multilingual coverage visible while the lane is still shaped by instrumental. · signals: manifest language counts, segment transcript refs, alignment windows
- **Caption and frame alignment trace** · Follow one spoken or sung moment across transcript, segment window, and frame reference. · signals: text/audio/video windows, coverage gaps, confidence per window
- **Silence and padding audit** · Catch dead air, over-long intros, and presentation choices that masquerade as meaningful model evidence. · signals: silence ratio, dynamic crest, tempo proxy, spectral flux
- **Chorus and repetition watch** · Measure when a catalog narrows around repeated hooks, loops, or production habits rooted in signal-study, reference. · signals: repetition ratio, beat stability, chroma summaries, genre coverage
