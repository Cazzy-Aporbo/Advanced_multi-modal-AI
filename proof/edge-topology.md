# Edge Gateway Topology

## Active policy

- jurisdiction: `EU_EEA`
- max entropy limit: `0.86`
- max zero ratio: `0.72`
- minimum finite ratio: `0.995`
- cross-border allowed: `False`
- encryption required: `True`

## Deployment artifacts

- `Dockerfile`
- `Makefile`
- `containers/compose.yaml`
- `containers/clickhouse-init.sql`
- `openapi/openapi.json`

## Transport lanes

- typed FastAPI contract edge
- connector-backed parquet and web intake
- generated Python and TypeScript client surfaces
- compiled Rust signal lane
- append-only tracking ledger

## Recent ledger events

- **hold** · `f50f9075-98b4-4c04-9527-623b5f2f653a` · DE → DE · entropy 0.894
- **hold** · `5b83f62c-a12c-40b6-b881-4d27a1c71489` · DE → DE · entropy 0.894
- **hold** · `70f69ca0-af64-45c9-af58-df5173e3bede` · DE → DE · entropy 0.894
- **hold** · `9638972a-41f8-4c61-9b55-d90b58e265ec` · DE → DE · entropy 0.894
- **hold** · `ccd0184c-be6e-4a71-b07c-e5a151062dde` · DE → DE · entropy 0.894
