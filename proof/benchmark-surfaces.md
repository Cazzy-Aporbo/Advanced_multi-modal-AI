# Reference Benchmark Surface

- Benchmark id: `a143ad94-f555-4dcf-a0be-0d0af3d515eb`
- Label: `public-reference-lane`
- Model id: `adaptive_transformer`
- Route count: `82`
- Verification artifacts: `10`
- Stage count: `9`
- Row count: `4`
- Pipeline run id: `465b2c1c-da1d-451f-9c3c-d1a65f5b9b7e`
- Replay frames: `8`
- Replay verified: `True`
- Total duration: `468.14` ms

## Notes

- This benchmark uses deterministic reference fixtures to exercise live repository lanes.
- It is meant to prove orchestration paths, persistence, and evidence export together.

## Stages

### Connector-backed Parquet ingest
- Stage id: `connector_ingest`
- Status: `pass`
- Duration: `141.46` ms
- Record count: `4`
- Artifacts: f131a6d7-ab0d-4c80-94ca-72dfbad08613, 465b2c1c-da1d-451f-9c3c-d1a65f5b9b7e
Notes:
  - pyarrow.parquet pulled 4 rows at 3052.2 rows/s.
  - Zero-copy candidate: yes.

### Pipeline replay ledger
- Stage id: `pipeline_replay`
- Status: `pass`
- Duration: `108.00` ms
- Record count: `8`
- Artifacts: 465b2c1c-da1d-451f-9c3c-d1a65f5b9b7e, replay_frames
Notes:
  - Replay frames sealed: 8.
  - Frame parity: verified.
  - Replay digest head: 9d02fb12399c5742…
  - Recorded head: 53ffd191e6d54716…
  - Replayed head: 53ffd191e6d54716…

### Cross-modal profile lane
- Stage id: `profile_lane`
- Status: `pass`
- Duration: `17.50` ms
- Record count: `2`
- Artifacts: /v1/data/profile
Notes:
  - Fusion readiness: 0.878.
  - Coverage score: 0.995.
  - Tensor intercept watch points: 2.

### Payload provenance receipt
- Stage id: `provenance_lane`
- Status: `pass`
- Duration: `0.31` ms
- Record count: `2`
- Artifacts: 3db334de-f9bf-4c88-8c9e-c0e407fc79b7
Notes:
  - Payload digest: f0f6dfabcbdc870c…
  - Metadata digest: 44136fa355b3678a…

### Persisted concurrent batch lane
- Stage id: `batch_job`
- Status: `pass`
- Duration: `86.16` ms
- Record count: `4`
- Artifacts: 76ed34d6-e716-49a8-84c4-2a856342fda3
Notes:
  - Workers used: 4 of 4 requested.
  - Median latency: 67.09 ms.
  - Failed items: 0.

### Recipe registry handoff
- Stage id: `recipe_compile`
- Status: `pass`
- Duration: `1.45` ms
- Record count: `1`
- Artifacts: eaff8068-0f02-4d2a-a7f1-37e37c14e598
Notes:
  - Distributed engine: local.
  - Resolved sources: 1.
  - Estimated global batch: 2.

### Segmented music feature warehouse
- Stage id: `music_warehouse`
- Status: `pass`
- Duration: `21.22` ms
- Record count: `3`
- Artifacts: 48fd35c9-d663-48c7-8e74-45efe17648c5, .runtime/music-feature-lake/reference-pulse-field-fd6bd215-20260703201352439153.parquet
Notes:
  - Feature table: .runtime/music-feature-lake/reference-pulse-field-fd6bd215-20260703201352439153.parquet.
  - Average entropy: 0.987.
  - Average tempo proxy: 0.0 bpm.

### Deterministic latency check
- Stage id: `smoke_benchmark`
- Status: `pass`
- Duration: `86.56` ms
- Record count: `6`
- Artifacts: 2bf94cef-e174-4f4d-a233-794f0daf4e2c
Notes:
  - Median latency: 14.27 ms.
  - P95 latency: 14.80 ms.

### Runtime proof surface snapshot
- Stage id: `proof_bundle`
- Status: `pass`
- Duration: `5.15` ms
- Record count: `10`
- Artifacts: proof/runtime-proof.json
Notes:
  - Route count: 82.
  - Verification artifacts: 10.
  - Connector kinds: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html.
