# Getting Started

## Run the API

```bash
uvicorn advanced_multimodal_ai.api:create_app --factory --reload
```

## Inspect the industrial routes

```bash
curl http://127.0.0.1:8000/v1/industrial/scenarios
```

## Run a diagnostic pass

```bash
python examples/diesel_engine.py
```

## Export the industrial proof bundle

```bash
python scripts/export_industrial_diagnostics.py
```

## Re-run the local verification lane

```bash
python3 -m ruff check src tests scripts
python3 -m pytest -q
cargo test -p multimodal-core
npm run --prefix sdk/typescript check
```
