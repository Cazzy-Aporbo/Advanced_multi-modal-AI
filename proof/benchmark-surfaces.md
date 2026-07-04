# Reference Benchmark Surface

- Benchmark id: `2e2e8da3-1635-4024-91be-139a75127ef5`
- Label: `public-reference-lane`
- Model id: `adaptive_transformer`
- Route count: `100`
- Verification artifacts: `16`
- Stage count: `9`
- Row count: `4`
- Pipeline run id: `0855b367-86cd-432a-83d8-0c3ae91f8a90`
- Replay frames: `8`
- Replay verified: `True`
- Total duration: `399.44` ms

## Notes

- This benchmark uses deterministic reference fixtures to exercise live repository lanes.
- It is meant to prove orchestration paths, persistence, and evidence export together.

## Stages

### Connector-backed Parquet ingest
- Stage id: `connector_ingest`
- Status: `pass`
- Duration: `114.12` ms
- Record count: `4`
- Artifacts: d7ad48db-55a2-407d-b113-e0722b0ffbca, 0855b367-86cd-432a-83d8-0c3ae91f8a90
Notes:
  - pyarrow.parquet pulled 4 rows at 3036.2 rows/s.
  - Zero-copy candidate: yes.

### Pipeline replay ledger
- Stage id: `pipeline_replay`
- Status: `pass`
- Duration: `86.99` ms
- Record count: `8`
- Artifacts: 0855b367-86cd-432a-83d8-0c3ae91f8a90, replay_frames
Notes:
  - Replay frames sealed: 8.
  - Frame parity: verified.
  - Replay digest head: 58e9747232f68538…
  - Recorded head: 9589417df27a4a7f…
  - Replayed head: 9589417df27a4a7f…

### Cross-modal profile lane
- Stage id: `profile_lane`
- Status: `pass`
- Duration: `15.66` ms
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
- Artifacts: ff1bae8f-cb33-4915-abc5-9ecdaef306aa
Notes:
  - Payload digest: f0f6dfabcbdc870c…
  - Metadata digest: 44136fa355b3678a…

### Persisted concurrent batch lane
- Stage id: `batch_job`
- Status: `pass`
- Duration: `74.38` ms
- Record count: `4`
- Artifacts: 19b5ed6d-5331-48b3-96c9-dd394799a192
Notes:
  - Workers used: 4 of 4 requested.
  - Median latency: 61.43 ms.
  - Failed items: 0.

### Recipe registry handoff
- Stage id: `recipe_compile`
- Status: `pass`
- Duration: `2.96` ms
- Record count: `1`
- Artifacts: a170671f-0582-4443-8e84-ea53b1b75b27
Notes:
  - Distributed engine: local.
  - Resolved sources: 1.
  - Estimated global batch: 2.

### Segmented music feature warehouse
- Stage id: `music_warehouse`
- Status: `pass`
- Duration: `22.82` ms
- Record count: `3`
- Artifacts: e91f378e-a350-4d1d-a364-0db26557a0cc, .runtime/music-feature-lake/reference-pulse-field-dc7fd746-20260704040305995032.parquet
Notes:
  - Feature table: .runtime/music-feature-lake/reference-pulse-field-dc7fd746-20260704040305995032.parquet.
  - Average entropy: 0.987.
  - Average tempo proxy: 0.0 bpm.

### Deterministic latency check
- Stage id: `smoke_benchmark`
- Status: `pass`
- Duration: `77.58` ms
- Record count: `6`
- Artifacts: 00f16945-e2c1-42e7-b92e-e434a38c8ef0
Notes:
  - Median latency: 12.91 ms.
  - P95 latency: 14.47 ms.

### Runtime proof surface snapshot
- Stage id: `proof_bundle`
- Status: `pass`
- Duration: `4.37` ms
- Record count: `16`
- Artifacts: proof/runtime-proof.json
Notes:
  - Route count: 100.
  - Verification artifacts: 16.
  - Connector kinds: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html.
