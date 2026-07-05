# Reference Benchmark Surface

- Benchmark id: `5810ce5f-c465-4a96-8be3-66ee295e126c`
- Label: `public-reference-lane`
- Model id: `adaptive_transformer`
- Route count: `106`
- Verification artifacts: `18`
- Stage count: `9`
- Row count: `4`
- Pipeline run id: `07fb83f6-b9f4-4902-b3d5-c5fbcf234038`
- Replay frames: `8`
- Replay verified: `True`
- Total duration: `421.50` ms

## Notes

- This benchmark uses deterministic reference fixtures to exercise live repository lanes.
- It is meant to prove orchestration paths, persistence, and evidence export together.

## Stages

### Connector-backed Parquet ingest
- Stage id: `connector_ingest`
- Status: `pass`
- Duration: `117.28` ms
- Record count: `4`
- Artifacts: be68600f-15c5-4404-bd93-a65c19a06c3e, 07fb83f6-b9f4-4902-b3d5-c5fbcf234038
Notes:
  - pyarrow.parquet pulled 4 rows at 2882.2 rows/s.
  - Zero-copy candidate: yes.

### Pipeline replay ledger
- Stage id: `pipeline_replay`
- Status: `pass`
- Duration: `94.26` ms
- Record count: `8`
- Artifacts: 07fb83f6-b9f4-4902-b3d5-c5fbcf234038, replay_frames
Notes:
  - Replay frames sealed: 8.
  - Frame parity: verified.
  - Replay digest head: 06924762d7165174…
  - Recorded head: 4f9a815282355451…
  - Replayed head: 4f9a815282355451…

### Cross-modal profile lane
- Stage id: `profile_lane`
- Status: `pass`
- Duration: `15.67` ms
- Record count: `2`
- Artifacts: /v1/data/profile
Notes:
  - Fusion readiness: 0.878.
  - Coverage score: 0.995.
  - Tensor intercept watch points: 2.

### Payload provenance receipt
- Stage id: `provenance_lane`
- Status: `pass`
- Duration: `0.26` ms
- Record count: `2`
- Artifacts: c872429a-ad58-4c41-9659-c7f7b55662cc
Notes:
  - Payload digest: f0f6dfabcbdc870c…
  - Metadata digest: 44136fa355b3678a…

### Persisted concurrent batch lane
- Stage id: `batch_job`
- Status: `pass`
- Duration: `73.30` ms
- Record count: `4`
- Artifacts: a0d00553-b864-42af-9eaa-043f8a302134
Notes:
  - Workers used: 4 of 4 requested.
  - Median latency: 68.30 ms.
  - Failed items: 0.

### Recipe registry handoff
- Stage id: `recipe_compile`
- Status: `pass`
- Duration: `2.99` ms
- Record count: `1`
- Artifacts: cb465f84-d9b9-40a3-afd5-9e9bc6ab5127
Notes:
  - Distributed engine: local.
  - Resolved sources: 1.
  - Estimated global batch: 2.

### Segmented music feature warehouse
- Stage id: `music_warehouse`
- Status: `pass`
- Duration: `23.55` ms
- Record count: `3`
- Artifacts: 755aeeab-70c3-4d7f-9c93-39fc427f36a1, .runtime/music-feature-lake/reference-pulse-field-2ab42bef-20260705154101128791.parquet
Notes:
  - Feature table: .runtime/music-feature-lake/reference-pulse-field-2ab42bef-20260705154101128791.parquet.
  - Average entropy: 0.987.
  - Average tempo proxy: 0.0 bpm.

### Deterministic latency check
- Stage id: `smoke_benchmark`
- Status: `pass`
- Duration: `88.74` ms
- Record count: `6`
- Artifacts: 45ea96e2-c0a8-4f8c-97e1-e1c4c1dcdc4c
Notes:
  - Median latency: 14.79 ms.
  - P95 latency: 15.20 ms.

### Runtime proof surface snapshot
- Stage id: `proof_bundle`
- Status: `pass`
- Duration: `5.25` ms
- Record count: `18`
- Artifacts: proof/runtime-proof.json
Notes:
  - Route count: 106.
  - Verification artifacts: 18.
  - Connector kinds: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html.
