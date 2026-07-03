# Reference Benchmark Surface

- Benchmark id: `9d9e14b6-6433-4416-a0c1-9fb73195f55c`
- Label: `public-reference-lane`
- Model id: `adaptive_transformer`
- Route count: `69`
- Verification artifacts: `9`
- Stage count: `8`
- Row count: `4`
- Pipeline run id: `605a75b1-02ac-4b57-b26e-6075df6211bf`
- Replay frames: `8`
- Replay verified: `True`
- Total duration: `693.26` ms

## Notes

- This benchmark uses deterministic reference fixtures to exercise live repository lanes.
- It is meant to prove orchestration paths, persistence, and evidence export together.

## Stages

### Connector-backed Parquet ingest
- Stage id: `connector_ingest`
- Status: `pass`
- Duration: `416.74` ms
- Record count: `4`
- Artifacts: 35a825aa-5a6f-40e9-9a7d-b3748a54f19f, 605a75b1-02ac-4b57-b26e-6075df6211bf
Notes:
  - pyarrow.parquet pulled 4 rows at 143.5 rows/s.
  - Zero-copy candidate: yes.

### Pipeline replay ledger
- Stage id: `pipeline_replay`
- Status: `pass`
- Duration: `91.47` ms
- Record count: `8`
- Artifacts: 605a75b1-02ac-4b57-b26e-6075df6211bf, replay_frames
Notes:
  - Replay frames sealed: 8.
  - Frame parity: verified.
  - Replay digest head: 245c0b7848cb33d1…
  - Recorded head: 7750b98918c1776c…
  - Replayed head: 7750b98918c1776c…

### Cross-modal profile lane
- Stage id: `profile_lane`
- Status: `pass`
- Duration: `16.14` ms
- Record count: `2`
- Artifacts: /v1/data/profile
Notes:
  - Fusion readiness: 0.878.
  - Coverage score: 0.995.
  - Tensor intercept watch points: 2.

### Payload provenance receipt
- Stage id: `provenance_lane`
- Status: `pass`
- Duration: `0.30` ms
- Record count: `2`
- Artifacts: 9f70bd24-3d10-4fb4-affe-f86a8819cc84
Notes:
  - Payload digest: f0f6dfabcbdc870c…
  - Metadata digest: 44136fa355b3678a…

### Persisted concurrent batch lane
- Stage id: `batch_job`
- Status: `pass`
- Duration: `69.35` ms
- Record count: `4`
- Artifacts: 59e53578-577c-4ccf-8bf7-defd9231d91a
Notes:
  - Workers used: 4 of 4 requested.
  - Median latency: 61.58 ms.
  - Failed items: 0.

### Recipe registry handoff
- Stage id: `recipe_compile`
- Status: `pass`
- Duration: `1.58` ms
- Record count: `1`
- Artifacts: 3ba795ef-46f0-416e-b676-b0100c9ac90a
Notes:
  - Distributed engine: local.
  - Resolved sources: 1.
  - Estimated global batch: 2.

### Deterministic latency check
- Stage id: `smoke_benchmark`
- Status: `pass`
- Duration: `92.02` ms
- Record count: `6`
- Artifacts: d3b59f2a-8a51-40d5-a6ea-3d5b5f41dfa4
Notes:
  - Median latency: 15.20 ms.
  - P95 latency: 15.42 ms.

### Runtime proof surface snapshot
- Stage id: `proof_bundle`
- Status: `pass`
- Duration: `5.50` ms
- Record count: `9`
- Artifacts: proof/runtime-proof.json
Notes:
  - Route count: 69.
  - Verification artifacts: 9.
  - Connector kinds: local_csv, local_jsonl, local_parquet, s3_parquet, http_json, http_ndjson, web_html.
