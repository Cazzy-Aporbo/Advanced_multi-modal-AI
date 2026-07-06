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

- **hold** · `83fab542-e1db-4f08-842a-7d98befad162` · DE → DE · entropy 0.894
- **hold** · `9bd76889-16ec-4aab-b8a0-a56e937c5370` · DE → DE · entropy 0.894
- **hold** · `ea07961b-1d72-4e6f-9b17-71f399892700` · DE → DE · entropy 0.894
- **hold** · `194e4c9e-8415-428e-92da-c2bf43840077` · DE → DE · entropy 0.894
- **hold** · `f50f9075-98b4-4c04-9527-623b5f2f653a` · DE → DE · entropy 0.894
- **hold** · `5b83f62c-a12c-40b6-b881-4d27a1c71489` · DE → DE · entropy 0.894
