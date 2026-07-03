# Executable examples

These examples are meant to reduce guesswork.

They do not describe an imaginary platform. They run against the repository's
actual FastAPI surface and write generated artifacts into `proof/`.

## One command to refresh the example bundle

```bash
python3 scripts/export_example_bundle.py
```

That command writes:

- `proof/example-bundle.json`
- `proof/example-bundle.md`

The bundle includes:

- contract-mode inference
- modality quality profiling
- connector-backed Parquet ingest
- public-web intake receipts
- compiled recipe manifest output
- transcript-first video cleanup
- smoke benchmark output
- runtime proof bundle summary
- runtime readiness report summary

## Local bring-up

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
uvicorn advanced_multimodal_ai.api:create_app --factory --host 0.0.0.0 --port 8000
```

Then open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/v1/health`
- `http://127.0.0.1:8000/v1/proof/bundle`
- `http://127.0.0.1:8000/v1/readiness/report`

## Useful local commands

```bash
python3 -m advanced_multimodal_ai.cli benchmark --iterations 3
python3 scripts/export_openapi.py
python3 scripts/generate_sdk_surfaces.py
python3 scripts/export_readiness_report.py
python3 scripts/build_runtime_proof_bundle.py
python3 scripts/run_acceptance_spine.py
```

## What the examples do not claim

- They do not claim a hidden distributed trainer.
- They do not store cloud credentials.
- They do not claim a production cluster that is absent from the repo.

They show the runtime edge, the evidence surfaces, and the generated artifacts
that are actually present here.
