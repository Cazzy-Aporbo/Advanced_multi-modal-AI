from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from advanced_multimodal_ai.api import create_app

    client = TestClient(create_app())

    client.post(
        "/v1/catalog/register",
        json={
            "dataset_name": "example_recipe_frames",
            "owner": "cazandra",
            "version": "2026.07.03",
            "modality": "image",
            "partition_keys": ["capture_day"],
            "primary_keys": ["frame_id"],
            "fields": [
                {"name": "frame_id", "dtype": "string", "nullable": False},
                {"name": "capture_day", "dtype": "date", "nullable": False},
                {"name": "image_uri", "dtype": "string", "nullable": False},
                {"name": "caption", "dtype": "string", "nullable": True},
            ],
            "tags": ["example", "recipe"],
        },
    )

    recipe_response = client.post(
        "/v1/recipes/compile",
        json={
            "label": "example-vision-language-recipe",
            "owner": "cazandra",
            "objective": "alignment_eval",
            "model": {
                "model_ref": "Qwen/Qwen2.5-VL-7B-Instruct",
                "family": "vision-language",
                "adapter_kind": "lora",
                "precision": "bf16",
                "target_modules": ["attn.q_proj", "attn.v_proj"],
            },
            "sources": [
                {
                    "split": "train",
                    "modality": "image",
                    "dataset_name": "example_recipe_frames",
                    "dataset_version": "2026.07.03",
                    "expected_rows": 240,
                }
            ],
            "training": {
                "epochs": 1.0,
                "micro_batch_size": 1,
                "gradient_accumulation_steps": 4,
            },
            "distributed": {
                "engine": "local",
                "node_count": 1,
                "devices_per_node": 1,
                "zero_stage": 0,
            },
            "evaluation": {
                "metrics": ["loss"],
                "primary_metric": "loss",
            },
            "tags": ["example"],
        },
    )
    recipe_response.raise_for_status()
    recipe_payload = recipe_response.json()

    with tempfile.TemporaryDirectory() as temp_dir:
        parquet_path = Path(temp_dir) / "example_signal.parquet"
        table = pa.table(
            {
                "event_id": ["evt-501", "evt-502", "evt-503"],
                "event_date": ["2026-07-03", "2026-07-04", "2026-07-05"],
                "sensor_a": [0.15, 0.25, 0.35],
                "sensor_b": [0.2, 0.3, 0.4],
                "tab_a": [0.95, 0.85, 0.75],
                "tab_b": [0.9, 0.8, 0.7],
            }
        )
        pq.write_table(table, parquet_path)

        connector_response = client.post(
            "/v1/connectors/pipeline-ingest",
            json={
                "connector": {"kind": "local_parquet", "source": str(parquet_path)},
                "dataset_name": "example_signal_rows",
                "owner": "cazandra",
                "version": "2026.07.03",
                "stream_id": "example-signal-stream",
                "batch_label": "example-window-01",
                "modality_mappings": [
                    {
                        "modality": "tabular",
                        "feature_fields": ["tab_a", "tab_b"],
                        "source": "example-tab-feed",
                    },
                    {
                        "modality": "sensor",
                        "feature_fields": ["sensor_a", "sensor_b"],
                        "source": "example-sensor-feed",
                    },
                ],
                "partition_key_field": "event_date",
            },
        )
        connector_response.raise_for_status()
        connector_payload = connector_response.json()

    infer_response = client.post(
        "/v1/infer",
        json={
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "classification",
            "num_classes": 3,
            "metadata": {"request_id": "example-infer-01"},
            "modalities": {
                "text": {"shape": [2, 4], "values": [0.1, 0.4, 0.7, 0.9, 0.2, 0.5, 0.6, 0.8]},
                "audio": {"shape": [2, 4], "values": [0.8, 0.6, 0.4, 0.2, 0.7, 0.5, 0.3, 0.1]},
            },
        },
    )
    infer_response.raise_for_status()
    infer_payload = infer_response.json()

    profile_response = client.post(
        "/v1/data/profile",
        json={
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "embedding",
            "metadata": {"request_id": "example-profile-01"},
            "modalities": {
                "text": {"shape": [2, 4], "values": [0.0, 0.3, 0.6, 0.9, 0.1, 0.4, 0.7, 1.0]},
                "audio": {"shape": [2, 4], "values": [0.2, 0.4, 0.5, 0.7, 0.3, 0.5, 0.6, 0.8]},
            },
        },
    )
    profile_response.raise_for_status()
    profile_payload = profile_response.json()

    video_response = client.post(
        "/v1/video/clean",
        json={
            "clip_id": "example-clip-01",
            "duration_ms": 4200,
            "transcript": [
                {"token": "um", "start_ms": 0, "end_ms": 220},
                {"token": "hello", "start_ms": 900, "end_ms": 1240},
                {"token": "world", "start_ms": 1320, "end_ms": 1600},
            ],
            "frames": [
                {
                    "index": 0,
                    "timestamp_ms": 120,
                    "motion_score": 0.18,
                    "focus_score": 0.82,
                    "brightness": 0.48,
                },
                {
                    "index": 1,
                    "timestamp_ms": 1100,
                    "motion_score": 0.31,
                    "focus_score": 0.74,
                    "brightness": 0.57,
                },
            ],
            "audio_energy": [
                {"timestamp_ms": 140, "energy": 0.42},
                {"timestamp_ms": 1080, "energy": 0.86},
            ],
        },
    )
    video_response.raise_for_status()
    video_payload = video_response.json()

    benchmark_response = client.get("/v1/benchmarks/smoke", params={"iterations": 3})
    benchmark_response.raise_for_status()
    benchmark_payload = benchmark_response.json()

    proof_response = client.get("/v1/proof/bundle")
    proof_response.raise_for_status()
    proof_payload = proof_response.json()

    readiness_response = client.get("/v1/readiness/report")
    readiness_response.raise_for_status()
    readiness_payload = readiness_response.json()

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "service": proof_payload["service"],
        "version": proof_payload["version"],
        "examples": {
            "inference": {
                "request_id": infer_payload["request_id"],
                "route": infer_payload["route"],
                "output_keys": sorted(infer_payload["outputs"].keys()),
                "warning_count": len(infer_payload["warnings"]),
            },
            "quality_profile": {
                "request_id": profile_payload["request_id"],
                "fusion_readiness": profile_payload["fusion_readiness"],
                "modality_count": len(profile_payload["modality_profiles"]),
                "warning_count": len(profile_payload["warnings"]),
            },
            "connector_ingest": {
                "run_id": connector_payload["connector_run"]["run_id"],
                "connector_kind": connector_payload["connector_run"]["connector_kind"],
                "record_count": connector_payload["connector_run"]["record_count"],
                "pipeline_run_id": connector_payload["pipeline_run"]["run_id"],
                "pipeline_status": connector_payload["pipeline_run"]["status"],
            },
            "recipe_manifest": {
                "recipe_id": recipe_payload["recipe_id"],
                "launcher": recipe_payload["launch_profile"]["launcher"],
                "engine": recipe_payload["launch_profile"]["engine"],
                "estimated_global_batch_size": (
                    recipe_payload["launch_profile"]["estimated_global_batch_size"]
                ),
                "resolved_sources": len(recipe_payload["resolved_sources"]),
            },
            "video_cleanup": {
                "clip_id": video_payload["clip_id"],
                "removed_span_count": len(video_payload["removed_spans"]),
                "retained_span_count": len(video_payload["retained_spans"]),
                "cut_script_lines": len(video_payload["cut_script"]),
            },
            "smoke_benchmark": {
                "benchmark_id": benchmark_payload["benchmark_id"],
                "model_id": benchmark_payload["model_id"],
                "iterations": benchmark_payload["iterations"],
                "median_latency_ms": benchmark_payload["median_latency_ms"],
                "p95_latency_ms": benchmark_payload["p95_latency_ms"],
            },
            "proof": {
                "route_count": proof_payload["route_count"],
                "test_count": proof_payload["test_count"],
                "verification_command_count": len(proof_payload["verification_commands"]),
                "connector_kinds": proof_payload["connector_kinds"],
            },
            "readiness": {
                "posture": readiness_payload["posture"],
                "compiled_recipe_count": readiness_payload["compiled_recipe_count"],
                "resolved_recipe_count": readiness_payload["resolved_recipe_count"],
                "check_names": [item["name"] for item in readiness_payload["checks"]],
            },
        },
    }

    proof_dir = ROOT / "proof"
    proof_dir.mkdir(parents=True, exist_ok=True)
    json_path = proof_dir / "example-bundle.json"
    markdown_path = proof_dir / "example-bundle.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(_render_markdown(payload), encoding="utf-8")
    print(json_path)
    print(markdown_path)


def _render_markdown(payload: dict) -> str:
    inference = payload["examples"]["inference"]
    profile = payload["examples"]["quality_profile"]
    connector = payload["examples"]["connector_ingest"]
    recipe = payload["examples"]["recipe_manifest"]
    video = payload["examples"]["video_cleanup"]
    benchmark = payload["examples"]["smoke_benchmark"]
    proof = payload["examples"]["proof"]
    readiness = payload["examples"]["readiness"]
    return f"""# Example Runtime Bundle

- Service: `{payload['service']}`
- Version: `{payload['version']}`
- Created at: `{payload['created_at']}`

## Inference

- Request id: `{inference['request_id']}`
- Route: `{', '.join(inference['route'])}`
- Output keys: `{', '.join(inference['output_keys'])}`

## Quality profile

- Fusion readiness: `{profile['fusion_readiness']}`
- Modality count: `{profile['modality_count']}`
- Warning count: `{profile['warning_count']}`

## Connector ingest

- Connector kind: `{connector['connector_kind']}`
- Record count: `{connector['record_count']}`
- Pipeline status: `{connector['pipeline_status']}`

## Recipe manifest

- Recipe id: `{recipe['recipe_id']}`
- Launcher: `{recipe['launcher']}`
- Engine: `{recipe['engine']}`
- Estimated global batch size: `{recipe['estimated_global_batch_size']}`

## Video cleanup

- Clip id: `{video['clip_id']}`
- Removed spans: `{video['removed_span_count']}`
- Retained spans: `{video['retained_span_count']}`

## Benchmark

- Benchmark id: `{benchmark['benchmark_id']}`
- Iterations: `{benchmark['iterations']}`
- Median latency ms: `{benchmark['median_latency_ms']}`
- P95 latency ms: `{benchmark['p95_latency_ms']}`

## Proof

- Route count: `{proof['route_count']}`
- Test count: `{proof['test_count']}`
- Verification commands: `{proof['verification_command_count']}`
- Connector kinds: `{', '.join(proof['connector_kinds'])}`

## Readiness

- Posture: `{readiness['posture']}`
- Compiled recipes: `{readiness['compiled_recipe_count']}`
- Resolved recipes: `{readiness['resolved_recipe_count']}`
- Checks: `{', '.join(readiness['check_names'])}`
"""


if __name__ == "__main__":
    main()
