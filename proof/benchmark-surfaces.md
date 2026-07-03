# Reference Benchmark Surface

- Benchmark id: `de5f65b7-90da-490f-9414-3838c7d3dd29`
- Label: `public-reference-lane`
- Model id: `adaptive_transformer`
- Route count: `69`
- Verification artifacts: `9`
- Stage count: `8`
- Row count: `4`
- Pipeline run id: `d6776f0f-b80d-494f-a242-1930e11d1b15`
- Replay frames: `8`
- Replay verified: `True`
- Total duration: `603.03` ms

## Notes

- This benchmark uses deterministic reference fixtures to exercise live repository lanes.
- It is meant to prove orchestration paths, persistence, and evidence export together.

## Stages

### Connector-backed Parquet ingest
- Stage id: `connector_ingest`
- Status: `pass`
- Duration: `346.39` ms
- Record count: `4`
- Artifacts: 46cad39f-c7c6-464c-ac3a-b6bcb1693cb9, d6776f0f-b80d-494f-a242-1930e11d1b15
Notes:
  - pyarrow.parquet pulled 4 rows at 153.0 rows/s.
  - Zero-copy candidate: yes.

### Pipeline replay ledger
- Stage id: `pipeline_replay`
- Status: `pass`
- Duration: `84.20` ms
- Record count: `8`
- Artifacts: d6776f0f-b80d-494f-a242-1930e11d1b15, replay_frames
Notes:
  - Replay frames sealed: 8.
  - Frame parity: verified.
  - Replay digest head: 57080e134ce3c4b5…
  - Recorded head: 6e234734f587683d…
  - Replayed head: 6e234734f587683d…

### Cross-modal profile lane
- Stage id: `profile_lane`
- Status: `pass`
- Duration: `15.60` ms
- Record count: `2`
- Artifacts: /v1/data/profile
Notes:
  - Fusion readiness: 0.878.
  - Coverage score: 0.995.
  - Tensor intercept watch points: 2.

### Payload provenance receipt
- Stage id: `provenance_lane`
- Status: `pass`
- Duration: `0.23` ms
- Record count: `2`
- Artifacts: 8d530fb4-e02f-485f-9a3e-78e8968146d8
Notes:
  - Payload digest: f0f6dfabcbdc870c…
  - Metadata digest: 44136fa355b3678a…

### Persisted concurrent batch lane
- Stage id: `batch_job`
- Status: `pass`
- Duration: `77.11` ms
- Record count: `4`
- Artifacts: 34b79e2a-360d-4e72-ad1f-8d821275d98c
Notes:
  - Workers used: 4 of 4 requested.
  - Median latency: 56.61 ms.
  - Failed items: 0.

### Recipe registry handoff
- Stage id: `recipe_compile`
- Status: `pass`
- Duration: `1.40` ms
- Record count: `1`
- Artifacts: 4251e043-9c03-41ea-a147-adfd6d9c8691
Notes:
  - Distributed engine: local.
  - Resolved sources: 1.
  - Estimated global batch: 2.

### Deterministic latency check
- Stage id: `smoke_benchmark`
- Status: `pass`
- Duration: `74.29` ms
- Record count: `6`
- Artifacts: 509161d7-dc7b-4391-9ff8-3dbad654062a
Notes:
  - Median latency: 12.29 ms.
  - P95 latency: 12.95 ms.

### Runtime proof surface snapshot
- Stage id: `proof_bundle`
- Status: `pass`
- Duration: `3.64` ms
- Record count: `9`
- Artifacts: proof/runtime-proof.json
Notes:
  - Route count: 69.
  - Verification artifacts: 9.
  - Connector kinds: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html.
