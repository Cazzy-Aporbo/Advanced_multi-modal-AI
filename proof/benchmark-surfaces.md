# Reference Benchmark Surface

- Benchmark id: `104bfb09-bd00-48cf-b3ac-211144ba54b6`
- Label: `public-reference-lane`
- Model id: `adaptive_transformer`
- Route count: `95`
- Verification artifacts: `16`
- Stage count: `9`
- Row count: `4`
- Pipeline run id: `bf5d6aea-ce4e-4481-9c26-d3b0a920df4c`
- Replay frames: `8`
- Replay verified: `True`
- Total duration: `423.21` ms

## Notes

- This benchmark uses deterministic reference fixtures to exercise live repository lanes.
- It is meant to prove orchestration paths, persistence, and evidence export together.

## Stages

### Connector-backed Parquet ingest
- Stage id: `connector_ingest`
- Status: `pass`
- Duration: `128.02` ms
- Record count: `4`
- Artifacts: 2bada704-5ff4-4803-8855-c598f2ab57f6, bf5d6aea-ce4e-4481-9c26-d3b0a920df4c
Notes:
  - pyarrow.parquet pulled 4 rows at 2348.6 rows/s.
  - Zero-copy candidate: yes.

### Pipeline replay ledger
- Stage id: `pipeline_replay`
- Status: `pass`
- Duration: `92.39` ms
- Record count: `8`
- Artifacts: bf5d6aea-ce4e-4481-9c26-d3b0a920df4c, replay_frames
Notes:
  - Replay frames sealed: 8.
  - Frame parity: verified.
  - Replay digest head: 93aad78b14e91d73…
  - Recorded head: dcd43efcf5ae7cf5…
  - Replayed head: dcd43efcf5ae7cf5…

### Cross-modal profile lane
- Stage id: `profile_lane`
- Status: `pass`
- Duration: `14.32` ms
- Record count: `2`
- Artifacts: /v1/data/profile
Notes:
  - Fusion readiness: 0.878.
  - Coverage score: 0.995.
  - Tensor intercept watch points: 2.

### Payload provenance receipt
- Stage id: `provenance_lane`
- Status: `pass`
- Duration: `0.25` ms
- Record count: `2`
- Artifacts: 1e28d23f-0553-42df-a690-9ac6e614a7cd
Notes:
  - Payload digest: f0f6dfabcbdc870c…
  - Metadata digest: 44136fa355b3678a…

### Persisted concurrent batch lane
- Stage id: `batch_job`
- Status: `pass`
- Duration: `74.79` ms
- Record count: `4`
- Artifacts: 50ed3ac8-9ee7-493f-9b0a-045d7a2c8a12
Notes:
  - Workers used: 4 of 4 requested.
  - Median latency: 62.58 ms.
  - Failed items: 0.

### Recipe registry handoff
- Stage id: `recipe_compile`
- Status: `pass`
- Duration: `1.82` ms
- Record count: `1`
- Artifacts: cc72c3df-6d8c-4d4a-bcd6-fb1b06d97437
Notes:
  - Distributed engine: local.
  - Resolved sources: 1.
  - Estimated global batch: 2.

### Segmented music feature warehouse
- Stage id: `music_warehouse`
- Status: `pass`
- Duration: `21.35` ms
- Record count: `3`
- Artifacts: 3d2b51da-8f14-4660-9a5e-bbcddfb8adb2, .runtime/music-feature-lake/reference-pulse-field-006d7792-20260704030130336971.parquet
Notes:
  - Feature table: .runtime/music-feature-lake/reference-pulse-field-006d7792-20260704030130336971.parquet.
  - Average entropy: 0.987.
  - Average tempo proxy: 0.0 bpm.

### Deterministic latency check
- Stage id: `smoke_benchmark`
- Status: `pass`
- Duration: `84.31` ms
- Record count: `6`
- Artifacts: 10c82fde-51c2-4d04-9b70-c11ceb6183f4
Notes:
  - Median latency: 14.16 ms.
  - P95 latency: 14.31 ms.

### Runtime proof surface snapshot
- Stage id: `proof_bundle`
- Status: `pass`
- Duration: `5.64` ms
- Record count: `16`
- Artifacts: proof/runtime-proof.json
Notes:
  - Route count: 95.
  - Verification artifacts: 16.
  - Connector kinds: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html.
