# Reference Benchmark Surface

- Benchmark id: `54cb1c02-76af-4aef-8fd8-e2e21b7eac74`
- Label: `public-reference-lane`
- Model id: `adaptive_transformer`
- Route count: `106`
- Verification artifacts: `18`
- Stage count: `9`
- Row count: `4`
- Pipeline run id: `aa84cf17-7192-490d-81c2-f6c5eeaa443e`
- Replay frames: `8`
- Replay verified: `True`
- Total duration: `423.38` ms

## Notes

- This benchmark uses deterministic reference fixtures to exercise live repository lanes.
- It is meant to prove orchestration paths, persistence, and evidence export together.

## Stages

### Connector-backed Parquet ingest
- Stage id: `connector_ingest`
- Status: `pass`
- Duration: `123.94` ms
- Record count: `4`
- Artifacts: 6ce551fc-162e-42d0-b5d5-179d21293003, aa84cf17-7192-490d-81c2-f6c5eeaa443e
Notes:
  - pyarrow.parquet pulled 4 rows at 2644.2 rows/s.
  - Zero-copy candidate: yes.

### Pipeline replay ledger
- Stage id: `pipeline_replay`
- Status: `pass`
- Duration: `90.27` ms
- Record count: `8`
- Artifacts: aa84cf17-7192-490d-81c2-f6c5eeaa443e, replay_frames
Notes:
  - Replay frames sealed: 8.
  - Frame parity: verified.
  - Replay digest head: 54dbb4a8b8fda309…
  - Recorded head: 3c58235e0e691374…
  - Replayed head: 3c58235e0e691374…

### Cross-modal profile lane
- Stage id: `profile_lane`
- Status: `pass`
- Duration: `15.90` ms
- Record count: `2`
- Artifacts: /v1/data/profile
Notes:
  - Fusion readiness: 0.878.
  - Coverage score: 0.995.
  - Tensor intercept watch points: 2.

### Payload provenance receipt
- Stage id: `provenance_lane`
- Status: `pass`
- Duration: `0.27` ms
- Record count: `2`
- Artifacts: 1cf69bd6-365e-40dd-8b12-2c41dd0e1586
Notes:
  - Payload digest: f0f6dfabcbdc870c…
  - Metadata digest: 44136fa355b3678a…

### Persisted concurrent batch lane
- Stage id: `batch_job`
- Status: `pass`
- Duration: `84.91` ms
- Record count: `4`
- Artifacts: 9070e175-440a-45a0-b882-79b6b11a3abd
Notes:
  - Workers used: 4 of 4 requested.
  - Median latency: 76.39 ms.
  - Failed items: 0.

### Recipe registry handoff
- Stage id: `recipe_compile`
- Status: `pass`
- Duration: `1.82` ms
- Record count: `1`
- Artifacts: 56147ee2-5e69-42da-94d0-b8e637571603
Notes:
  - Distributed engine: local.
  - Resolved sources: 1.
  - Estimated global batch: 2.

### Segmented music feature warehouse
- Stage id: `music_warehouse`
- Status: `pass`
- Duration: `23.77` ms
- Record count: `3`
- Artifacts: 0d7e3aa9-eed0-49cc-b76a-8cd63f9b08b7, .runtime/music-feature-lake/reference-pulse-field-7b8e5688-20260706003210798918.parquet
Notes:
  - Feature table: .runtime/music-feature-lake/reference-pulse-field-7b8e5688-20260706003210798918.parquet.
  - Average entropy: 0.987.
  - Average tempo proxy: 0.0 bpm.

### Deterministic latency check
- Stage id: `smoke_benchmark`
- Status: `pass`
- Duration: `77.65` ms
- Record count: `6`
- Artifacts: 51da574a-ebc0-4b52-81af-10d5663bb38e
Notes:
  - Median latency: 13.23 ms.
  - P95 latency: 13.89 ms.

### Runtime proof surface snapshot
- Stage id: `proof_bundle`
- Status: `pass`
- Duration: `4.69` ms
- Record count: `18`
- Artifacts: proof/runtime-proof.json
Notes:
  - Route count: 106.
  - Verification artifacts: 18.
  - Connector kinds: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html.
