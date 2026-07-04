# Industry Profiles

The runtime lanes can be read across domains without pretending each field has the
same evidence burden. These profiles stay tied to routes and proof surfaces that
already exist in the repository.

## Healthcare

- modalities: text, tabular, audio, image
- anchor routes: `/v1/catalog/register`, `/v1/drift/check`, `/v1/ontology/liability`, `/v1/data/provenance`
- strict checks: schema fingerprinting before downstream reuse, population-entry drift before cohort transfer, provenance receipts for repeated chart review
- supply chain focus: Watch how annotations, clinical exports, and downstream feature tables inherit the same residency and retention rules.
- signal questions: Did the measured population shift before the model changed?, Which record stayed closest to the final decision path?
- proof surfaces: `proof/runtime-proof.json`, `proof/research-surfaces.json`

## Employment

- modalities: text, audio, tabular
- anchor routes: `/v1/catalog/evolution`, `/v1/bias/assess`, `/v1/drift/check`, `/v1/edge/evaluate`
- strict checks: stage-aware bias review, dataset evolution checks before ranking logic moves, edge routing review for cross-border applicant data
- supply chain focus: Keep interview transcripts, score tables, and exported decisions tied to the same change-control record.
- signal questions: Where did representational narrowing enter the process?, Which review lane can still interrupt a bad automation path?
- proof surfaces: `proof/operator-surfaces.json`, `proof/edge-topology.json`

## Education

- modalities: text, audio, image
- anchor routes: `/v1/video/packet`, `/v1/video/clean`, `/v1/alignment/windows`, `/v1/drift/check`
- strict checks: transcript-first video packetization, alignment windows before lesson claims are summarized, drift baselines for language and access patterns
- supply chain focus: Keep the handoff from lecture capture to cleaned teaching asset visible enough for a teacher to question it.
- signal questions: Did cleanup remove context instead of noise?, Which modality stayed behind when comprehension dropped?
- proof surfaces: `proof/benchmark-surfaces.json`, `proof/cymatic-surface.json`

## Business operations

- modalities: text, tabular, image
- anchor routes: `/v1/ontology/ingest`, `/v1/ontology/liability`, `/v1/recipes/compile`, `/v1/jobs/batch-infer`
- strict checks: ontology snapshots tied to workflow claims, liability surfacing before orchestration expands, batch receipts with persisted run records
- supply chain focus: Keep contracts, workflow rules, and exported decisions readable as one chain instead of three adjacent systems.
- signal questions: Which rule lives in code, and which one still lives in memory?, Can the batch lane be replayed without improvising missing context?
- proof surfaces: `proof/example-bundle.json`, `proof/repository-pulse.json`

## Sports

- modalities: video, audio, tabular, text
- anchor routes: `/v1/video/packet`, `/v1/alignment/windows`, `/v1/pipelines/runs/{run_id}/export`, `/v1/data/provenance`
- strict checks: temporal alignment around event windows, replay parity before highlight or review claims, provenance receipts for contested moments
- supply chain focus: Preserve which camera, commentary slice, and metric feed shaped a single segment-level judgment.
- signal questions: Which modality disagreed first when the sequence changed?, Can a disputed replay be reconstructed from stored evidence alone?
- proof surfaces: `proof/benchmark-surfaces.json`, `proof/execution-journal.json`

## Media

- modalities: audio, text, video, image
- anchor routes: `/v1/music/features/extract`, `/v1/music/drift`, `/v1/music/proof/change-report`, `/v1/benchmarks/reference`
- strict checks: manifest-only audio intake, segment index plus derived feature warehouse, language-share and loudness drift monitoring
- supply chain focus: Keep track references, feature runs, embeddings, and drift receipts closer than the public story built on them.
- signal questions: Is repetition entering through production polish rather than taste?, Which catalog shift is visible before the ranking layer notices it?
- proof surfaces: `proof/music-observatory.json`, `proof/cymatic-surface.json`

## Journalism

- modalities: text, audio, image, video
- anchor routes: `/v1/data/provenance`, `/v1/edge/evaluate`, `/v1/video/clean`, `/v1/ontology/liability`
- strict checks: receipt issuance for repeated claims, edge evaluation before cross-border publication lanes, cleanup planning that preserves attribution
- supply chain focus: Treat source movement, transcript cleanup, and downstream publication as one auditable chain.
- signal questions: Which asset can still defend the claim if a quote is challenged?, Did cleanup preserve meaning or only remove friction?
- proof surfaces: `proof/edge-topology.json`, `proof/example-bundle.json`

## Dentistry

- modalities: image, text, tabular
- anchor routes: `/v1/catalog/register`, `/v1/data/provenance`, `/v1/drift/check`, `/v1/edge/evaluate`
- strict checks: contract registration before image-derived fields expand, population drift checks for narrow cohorts, edge review before external routing
- supply chain focus: Keep imaging derivatives, care-plan notes, and exported follow-up artifacts under one review rhythm.
- signal questions: Did the image-derived feature move farther than the chart note?, Which cohort assumption became too narrow to reuse safely?
- proof surfaces: `proof/runtime-proof.json`, `proof/edge-topology.json`

## Biology

- modalities: tabular, image, text
- anchor routes: `/v1/catalog/register`, `/v1/data/profile`, `/v1/alignment/windows`, `/v1/data/provenance`
- strict checks: field-level dataset registration, quality profiling before fusion, alignment windows for paired assay and image slices
- supply chain focus: Watch how specimen metadata, measurement tables, and image windows separate or stay coupled through export.
- signal questions: Which finite detail disappeared when the table was cleaned?, Can the microscopy slice still be traced from result back to source?
- proof surfaces: `proof/research-surfaces.json`, `proof/runtime-proof.json`

## Industrial diagnostics

- modalities: text, tabular, audio, image
- anchor routes: `/v1/industrial/scenarios`, `/v1/industrial/diagnose`, `/v1/industrial/model-check`, `/v1/edge/evaluate`
- strict checks: formal trace checks before restart, lockout and guard verification before intervention, proof-tree and audit-chain generation for each diagnostic pass
- supply chain focus: Keep machine symptoms, sensor drift, safety obligations, and final maintenance posture sealed into one diagnostic chain.
- signal questions: Which fault path became visible before the field team touched the machine?, Can restart logic still be defended if the trace is replayed later?
- proof surfaces: `proof/industrial-diagnostics.json`, `proof/edge-topology.json`

## Construction

- modalities: image, video, tabular, text
- anchor routes: `/v1/stewardship/supply-chain`, `/v1/recipes/compile`, `/v1/video/packet`, `/v1/pipelines/runs/{run_id}/export`
- strict checks: supply-chain edge review, recipe compilation with proof obligations, video windowing around site events
- supply chain focus: Track how vendor files, site imagery, and schedule deltas enter the same operational account.
- signal questions: Which downstream delay came from missing evidence rather than late work?, Can a site event be replayed with the same context later?
- proof surfaces: `proof/repository-pulse.json`, `proof/benchmark-surfaces.json`

## Supply chain

- modalities: tabular, text, image
- anchor routes: `/v1/stewardship/supply-chain`, `/v1/stewardship/change-controls`, `/v1/ontology/liability`, `/v1/edge/evaluate`
- strict checks: governed edge mapping, change-control records before route shifts, liability surfacing against stated obligations
- supply chain focus: Keep source nodes, destination nodes, deletion posture, and cross-border edges visible in the same record.
- signal questions: Which ungoverned edge still carries business-critical data?, Did the route expand before the control surface changed with it?
- proof surfaces: `proof/runtime-proof.json`, `proof/edge-topology.json`

