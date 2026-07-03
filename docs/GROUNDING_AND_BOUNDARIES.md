# Grounding and Boundaries

This repository is built to be read in two ways at once.

It should be useful to engineers who want executable multimodal infrastructure,
and it should remain candid about what is still a research lane, what is a
reference fixture, and what still deserves human review before it travels into
heavier operational settings.

## 1. What is being claimed

The live repository claim is narrower than the research ambition.

The live claim is that the repository can:

- serve a typed FastAPI runtime
- register dataset contracts from real connector-fed rows
- ingest multimodal pipeline runs through explicit mappings
- profile signal quality, sparsity, entropy, and alignment
- issue provenance receipts and export runtime proof bundles
- persist replay frames and verify replay parity on saved runs
- compile recipes, generate OpenAPI contracts, and regenerate client surfaces
- keep an execution journal showing which export and validation lanes ran

The repository does **not** claim that every research model present here is
already ready for high-concurrency production deployment. That distinction is
intentional and visible in the code layout, the research surfaces, and the
benchmark lane.

## 2. What counts as real input here

The repository accepts several source shapes through the connector lane:

- local CSV
- local NDJSON
- local Parquet
- S3-shaped Parquet objects
- HTTP JSON
- HTTP NDJSON
- bounded public HTML pages

Those inputs are materialized into typed rows before they are mapped into
tensor payloads or pipeline events. This keeps the ingestion lane inspectable.

Reference benchmark fixtures are still used in places where determinism matters
more than novelty, especially for replay, regression, and export proof. Those
fixtures are deterministic on purpose. They are not offered as a substitute for
field data, and they are kept separate from connector-fed evidence.

## 3. What the web intake lane is allowed to do

The public-web lane is a measured intake path, not an indiscriminate crawler.

The current implementation in
[`src/advanced_multimodal_ai/connectors.py`](../src/advanced_multimodal_ai/connectors.py)
and the web contract models in
[`src/advanced_multimodal_ai/contracts.py`](../src/advanced_multimodal_ai/contracts.py)
apply these boundaries:

- domain allowlists can be declared before a fetch begins
- `robots.txt` can be checked before page bodies are read
- per-domain request intervals can be enforced when recent receipts exist
- byte caps limit oversized pulls
- fetch receipts are persisted beside extracted rows

That means the repository can be used for careful public-domain intake and
review work without pretending that every possible web acquisition path is
acceptable.

## 4. Data stewardship is part of the runtime

Lifecycle, half-life, residency, and removal concerns are treated as data-plane
controls rather than documentation garnish.

The stewardship lane covers:

- lifecycle policies tied to named dataset contracts
- change-control records tied to affected routes and validations
- supply-chain snapshots from source to consumer
- posture summaries that show what is covered and what is still exposed

Relevant modules:

- [`src/advanced_multimodal_ai/stewardship.py`](../src/advanced_multimodal_ai/stewardship.py)
- [`src/advanced_multimodal_ai/stewardship_store.py`](../src/advanced_multimodal_ai/stewardship_store.py)
- [`src/advanced_multimodal_ai/catalog.py`](../src/advanced_multimodal_ai/catalog.py)
- [`src/advanced_multimodal_ai/catalog_store.py`](../src/advanced_multimodal_ai/catalog_store.py)

This is especially important for educational use. It gives learners and
reviewers a visible example of how dataset management, change control, and
runtime operations can remain close to one another.

## 5. Proof comes from regeneration, not memory

The repository is structured so the public surface can be refreshed from the
runtime rather than rewritten by hand.

The main proof and export commands are:

```bash
python3 scripts/build_runtime_proof_bundle.py
python3 scripts/export_repository_pulse.py
python3 scripts/export_research_surfaces.py
python3 scripts/export_execution_journal.py
python3 scripts/export_readiness_report.py
python3 scripts/export_benchmark_surfaces.py
python3 scripts/export_openapi.py
python3 scripts/generate_sdk_surfaces.py
python3 scripts/run_acceptance_spine.py
```

Those commands regenerate:

- runtime proof
- repository pulse
- research surfaces
- execution journal
- readiness report
- benchmark surfaces
- OpenAPI contracts
- generated client SDKs

The browser-facing pages read those generated artifacts. They are not supposed
to drift into a separate story.

Property-based coverage now sits inside the ordinary pytest lane as well. The
repository uses that lane to throw varied tensor shapes, intercept conditions,
and connector-row faults at the same runtime contracts the API already uses.

## 6. What still needs a human

There are still decisions a repository should not make alone.

Human review remains important when:

- a dataset introduces new fields with unclear consent or provenance
- a public-web source has terms, robots posture, or attribution rules that are
  still ambiguous
- a model card is being promoted from research archive status into a live
  runtime lane
- a drift delta is technically measurable but operationally uncertain
- supply-chain records show legal or residency conflicts that need domain
  judgment rather than blind automation

The repository can surface those tensions. It should not pretend to resolve all
of them silently.

## 7. Educational posture

The project is meant to be useful in teaching and self-study because it keeps
several usually disconnected concerns together:

- typed API contracts
- compiled signal primitives
- proof regeneration
- replay discipline
- dataset stewardship
- connector benchmarking
- model cards tied back to code

It is therefore a software repository, a runtime workbench, and a learning
surface at once. Those roles are compatible when the boundaries stay visible.

## 8. License, attribution, and contribution posture

This repository is released under the Apache License 2.0. The copyright and
attribution posture is intentionally plain:

- authorship is credited in [`pyproject.toml`](../pyproject.toml)
- the governing license is in [`LICENSE`](../LICENSE)
- attribution and notice expectations are recorded in [`NOTICE`](../NOTICE)

Contributions are welcome when they strengthen the executable surface, the
generated proof path, the reproducibility of the research, or the clarity of
the public learning surfaces.

## 9. A concise reading of the repository

If a reviewer wants the shortest honest description:

The repository already runs a meaningful multimodal runtime edge. It also keeps
research branches and larger ambitions visible. The important discipline is
that the two are not blurred together. Public pages, proof exports, replay
artifacts, SDKs, and stewardship records should all continue to make that
distinction easy to verify.
