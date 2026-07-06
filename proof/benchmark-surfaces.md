# Reference Benchmark Surface

- Benchmark id: `e5f1f92a-4bfa-4123-aec6-8d3cba5ec883`
- Label: `public-reference-lane`
- Model id: `adaptive_transformer`
- Route count: `106`
- Verification artifacts: `18`
- Stage count: `9`
- Row count: `4`
- Pipeline run id: `51d6e8c2-1f8c-4ef6-b3c8-1b97c66d64e8`
- Replay frames: `8`
- Replay verified: `True`
- Total duration: `410.66` ms

## Notes

- This benchmark uses deterministic reference fixtures to exercise live repository lanes.
- It is meant to prove orchestration paths, persistence, and evidence export together.

## Stages

### Connector-backed Parquet ingest
- Stage id: `connector_ingest`
- Status: `pass`
- Duration: `121.90` ms
- Record count: `4`
- Artifacts: e82f09f3-b4c8-494f-911c-92f786c19b90, 51d6e8c2-1f8c-4ef6-b3c8-1b97c66d64e8
Notes:
  - pyarrow.parquet pulled 4 rows at 3217.3 rows/s.
  - Zero-copy candidate: yes.

### Pipeline replay ledger
- Stage id: `pipeline_replay`
- Status: `pass`
- Duration: `90.28` ms
- Record count: `8`
- Artifacts: 51d6e8c2-1f8c-4ef6-b3c8-1b97c66d64e8, replay_frames
Notes:
  - Replay frames sealed: 8.
  - Frame parity: verified.
  - Replay digest head: 37e5af5e465b1d8a…
  - Recorded head: c21ef7d131bcfd9d…
  - Replayed head: c21ef7d131bcfd9d…

### Cross-modal profile lane
- Stage id: `profile_lane`
- Status: `pass`
- Duration: `14.99` ms
- Record count: `2`
- Artifacts: /v1/data/profile
Notes:
  - Fusion readiness: 0.878.
  - Coverage score: 0.995.
  - Tensor intercept watch points: 2.

### Payload provenance receipt
- Stage id: `provenance_lane`
- Status: `pass`
- Duration: `0.36` ms
- Record count: `2`
- Artifacts: fb199153-d6bd-44e7-9534-f4c3689b14a4
Notes:
  - Payload digest: f0f6dfabcbdc870c…
  - Metadata digest: 44136fa355b3678a…

### Persisted concurrent batch lane
- Stage id: `batch_job`
- Status: `pass`
- Duration: `76.33` ms
- Record count: `4`
- Artifacts: ed62f458-429d-43f1-8ff3-3477229a21d4
Notes:
  - Workers used: 4 of 4 requested.
  - Median latency: 64.74 ms.
  - Failed items: 0.

### Recipe registry handoff
- Stage id: `recipe_compile`
- Status: `pass`
- Duration: `1.87` ms
- Record count: `1`
- Artifacts: fc9012e1-64b1-450b-978c-abf2edf811ad
Notes:
  - Distributed engine: local.
  - Resolved sources: 1.
  - Estimated global batch: 2.

### Segmented music feature warehouse
- Stage id: `music_warehouse`
- Status: `pass`
- Duration: `23.08` ms
- Record count: `3`
- Artifacts: d11c20f7-3319-4700-bba6-5fa40e4ed39f, .runtime/music-feature-lake/reference-pulse-field-4251decb-20260706004858903285.parquet
Notes:
  - Feature table: .runtime/music-feature-lake/reference-pulse-field-4251decb-20260706004858903285.parquet.
  - Average entropy: 0.987.
  - Average tempo proxy: 0.0 bpm.

### Deterministic latency check
- Stage id: `smoke_benchmark`
- Status: `pass`
- Duration: `76.81` ms
- Record count: `6`
- Artifacts: edaf2294-0b79-4a98-8908-c571d1ea571d
Notes:
  - Median latency: 12.79 ms.
  - P95 latency: 13.14 ms.

### Runtime proof surface snapshot
- Stage id: `proof_bundle`
- Status: `pass`
- Duration: `4.84` ms
- Record count: `18`
- Artifacts: proof/runtime-proof.json
Notes:
  - Route count: 106.
  - Verification artifacts: 18.
  - Connector kinds: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html.
