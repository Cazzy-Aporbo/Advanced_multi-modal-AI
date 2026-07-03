from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from advanced_multimodal_ai import connectors as connector_module
    from advanced_multimodal_ai.api import create_app

    client = TestClient(create_app())

    baseline = client.post(
        "/v1/drift/baselines",
        json={
            "label": "acceptance-baseline",
            "request": {
                "model_id": "adaptive_transformer",
                "runtime_mode": "contract",
                "target": "embedding",
                "metadata": {"request_id": "acceptance-baseline"},
                "modalities": {
                    "text": {
                        "shape": [2, 4],
                        "values": [0.1, 0.2, 0.3, 0.4, 0.2, 0.3, 0.4, 0.5],
                    },
                    "audio": {
                        "shape": [2, 4],
                        "values": [0.4, 0.3, 0.2, 0.1, 0.5, 0.4, 0.3, 0.2],
                    },
                },
            },
        },
    )
    assert baseline.status_code == 200, baseline.text

    dataset = client.post(
        "/v1/catalog/register",
        json={
            "dataset_name": "acceptance_events",
            "owner": "cazandra",
            "version": "1.0.0",
            "modality": "tabular",
            "partition_keys": ["event_date"],
            "primary_keys": ["event_id"],
            "fields": [
                {"name": "event_id", "dtype": "string", "nullable": False},
                {"name": "event_date", "dtype": "date", "nullable": False},
                {"name": "artist_id", "dtype": "string", "nullable": False},
            ],
        },
    )
    assert dataset.status_code == 200, dataset.text

    recipe = client.post(
        "/v1/recipes/compile",
        json={
            "label": "acceptance-recipe",
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
                    "modality": "tabular",
                    "dataset_name": "acceptance_events",
                    "dataset_version": "1.0.0",
                    "expected_rows": 2,
                }
            ],
            "training": {
                "epochs": 1.0,
                "micro_batch_size": 1,
                "gradient_accumulation_steps": 2,
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
        },
    )
    assert recipe.status_code == 200, recipe.text
    recipe_id = recipe.json()["recipe_id"]

    with tempfile.TemporaryDirectory() as temp_dir:
        recipe_manifest_path = Path(temp_dir) / "acceptance_recipe.json"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "advanced_multimodal_ai.cli",
                "recipe-export",
                "--recipe-id",
                recipe_id,
                "--output",
                str(recipe_manifest_path),
            ],
            check=True,
        )
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_recipe_manifest.py"),
                str(recipe_manifest_path),
            ],
            check=True,
        )

        csv_path = Path(temp_dir) / "acceptance_signal.csv"
        csv_path.write_text(
            "\n".join(
                [
                    "event_id,event_date,sensor_a,sensor_b,tab_a,tab_b",
                    "evt-1,2026-07-01,0.1,0.2,1.0,0.9",
                    "evt-2,2026-07-02,0.2,0.3,0.9,0.8",
                ]
            ),
            encoding="utf-8",
        )

        connector = client.post(
            "/v1/connectors/pipeline-ingest",
            json={
                "connector": {"kind": "local_csv", "source": str(csv_path)},
                "dataset_name": "acceptance_signal_rows",
                "owner": "cazandra",
                "version": "1.0.0",
                "stream_id": "acceptance-connector-stream",
                "batch_label": "window-connector",
                "modality_mappings": [
                    {
                        "modality": "tabular",
                        "feature_fields": ["tab_a", "tab_b"],
                        "source": "tab-feed",
                    },
                    {
                        "modality": "sensor",
                        "feature_fields": ["sensor_a", "sensor_b"],
                        "source": "sensor-feed",
                    },
                ],
            },
        )
        assert connector.status_code == 200, connector.text

        parquet_path = Path(temp_dir) / "acceptance_signal.parquet"
        parquet_table = pa.table(
            {
                "event_id": ["evt-11", "evt-12"],
                "event_date": ["2026-07-11", "2026-07-12"],
                "sensor_a": [0.11, 0.22],
                "sensor_b": [0.21, 0.32],
                "tab_a": [0.91, 0.81],
                "tab_b": [0.88, 0.78],
            }
        )
        pq.write_table(parquet_table, parquet_path)

        parquet_connector = client.post(
            "/v1/connectors/pipeline-ingest",
            json={
                "connector": {"kind": "local_parquet", "source": str(parquet_path)},
                "dataset_name": "acceptance_signal_parquet",
                "owner": "cazandra",
                "version": "1.0.1",
                "stream_id": "acceptance-parquet-stream",
                "batch_label": "window-parquet",
                "modality_mappings": [
                    {
                        "modality": "tabular",
                        "feature_fields": ["tab_a", "tab_b"],
                        "source": "parquet-tab-feed",
                    },
                    {
                        "modality": "sensor",
                        "feature_fields": ["sensor_a", "sensor_b"],
                        "source": "parquet-sensor-feed",
                    },
                ],
            },
        )
        assert parquet_connector.status_code == 200, parquet_connector.text

        output = pa.BufferOutputStream()
        s3_table = pa.table(
            {
                "event_id": ["evt-21", "evt-22"],
                "event_date": ["2026-07-21", "2026-07-22"],
                "sensor_a": [0.14, 0.24],
                "sensor_b": [0.18, 0.28],
                "tab_a": [0.94, 0.84],
                "tab_b": [0.89, 0.79],
            }
        )
        pq.write_table(s3_table, output)
        s3_bytes = output.getvalue().to_pybytes()

        class FakeBody:
            def read(self) -> bytes:
                return s3_bytes

        class FakeS3Client:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def get_object(self, *, Bucket: str, Key: str):
                assert Bucket == "loopchii-acceptance"
                assert Key == "acceptance/music_signal.parquet"
                assert self.kwargs["region_name"] == "us-east-1"
                return {"Body": FakeBody()}

        class FakeBoto3:
            def client(self, service_name: str, **kwargs):
                assert service_name == "s3"
                assert kwargs["aws_access_key_id"] == "acceptance-access"
                assert kwargs["aws_secret_access_key"] == "acceptance-secret"
                return FakeS3Client(**kwargs)

        connector_module.boto3 = FakeBoto3()
        os.environ["AMAI_ACCEPTANCE_AWS_ACCESS_KEY_ID"] = "acceptance-access"
        os.environ["AMAI_ACCEPTANCE_AWS_SECRET_ACCESS_KEY"] = "acceptance-secret"

        s3_connector = client.post(
            "/v1/connectors/pipeline-ingest",
            json={
                "connector": {
                    "kind": "s3_parquet",
                    "source": "s3://loopchii-acceptance/acceptance/music_signal.parquet",
                    "region": "us-east-1",
                    "secret_env": {
                        "aws_access_key_id": "AMAI_ACCEPTANCE_AWS_ACCESS_KEY_ID",
                        "aws_secret_access_key": "AMAI_ACCEPTANCE_AWS_SECRET_ACCESS_KEY",
                    },
                },
                "dataset_name": "acceptance_signal_s3",
                "owner": "cazandra",
                "version": "1.0.2",
                "stream_id": "acceptance-s3-stream",
                "batch_label": "window-s3",
                "modality_mappings": [
                    {
                        "modality": "tabular",
                        "feature_fields": ["tab_a", "tab_b"],
                        "source": "s3-tab-feed",
                    },
                    {
                        "modality": "sensor",
                        "feature_fields": ["sensor_a", "sensor_b"],
                        "source": "s3-sensor-feed",
                    },
                ],
            },
        )
        assert s3_connector.status_code == 200, s3_connector.text

    pipeline = client.post(
        "/v1/pipelines/ingest",
        json={
            "stream_id": "acceptance-stream",
            "batch_label": "window-01",
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "embedding",
            "baseline_label": "acceptance-baseline",
            "events": [
                {
                    "source": "caption-feed",
                    "modality": "text",
                    "tensor": {"shape": [1, 4], "values": [0.1, 0.2, 0.3, 0.4]},
                },
                {
                    "source": "caption-feed",
                    "modality": "text",
                    "tensor": {"shape": [1, 4], "values": [0.2, 0.3, 0.4, 0.5]},
                },
                {
                    "source": "audio-feed",
                    "modality": "audio",
                    "tensor": {"shape": [1, 4], "values": [0.4, 0.3, 0.2, 0.1]},
                },
                {
                    "source": "audio-feed",
                    "modality": "audio",
                    "tensor": {"shape": [1, 4], "values": [0.5, 0.4, 0.3, 0.2]},
                },
            ],
        },
    )
    assert pipeline.status_code == 200, pipeline.text
    pipeline_payload = pipeline.json()

    replay = client.post(f"/v1/pipelines/runs/{pipeline_payload['run_id']}/replay")
    assert replay.status_code == 200, replay.text
    replay_payload = replay.json()
    assert replay_payload["frame_parity_match"] is True
    assert replay_payload["provenance_match"] is True

    benchmark = client.get("/v1/benchmarks/reference")
    assert benchmark.status_code == 200, benchmark.text
    benchmark_payload = benchmark.json()
    assert benchmark_payload["replay_verified"] is True
    assert benchmark_payload["replay_frame_count"] >= 1

    snapshot = client.post(
        "/v1/ontology/ingest",
        json={
            "tenant_id": "acceptance-tenant",
            "label": "acceptance-ontology",
            "artifacts": [
                {
                    "title": "Treasury route",
                    "artifact_type": "api_schema",
                    "control_depth": "surface",
                    "body": "POST /finance/transfer routes transfer requests.",
                },
                {
                    "title": "Treasury policy",
                    "artifact_type": "contract",
                    "control_depth": "governance",
                    "body": (
                        "The route /finance/transfer shall not move financial data from EU to US. "
                        "All transfers must stay encrypted in transit."
                    ),
                    "tags": ["financial", "encrypt"],
                },
            ],
        },
    )
    assert snapshot.status_code == 200, snapshot.text
    snapshot_id = snapshot.json()["snapshot_id"]

    liability = client.post(
        "/v1/ontology/liability",
        json={
            "snapshot_id": snapshot_id,
            "traces": [
                {
                    "route": "/finance/transfer",
                    "action": "export",
                    "source_region": "EU",
                    "destination_region": "US",
                    "transport_encrypted": False,
                    "data_categories": ["financial"],
                    "metadata": {"reviewed": False},
                }
            ],
        },
    )
    assert liability.status_code == 200, liability.text

    bias = client.post(
        "/v1/bias/assess",
        json={
            "system_name": "acceptance-runtime",
            "active_stages": ["measurement", "retrieval", "governance"],
            "observed_signals": ["sensor", "ranking", "feedback", "drift"],
            "data_categories": ["biometric", "pii"],
        },
    )
    assert bias.status_code == 200, bias.text

    attestation = client.get("/v1/runtime/attestation")
    assert attestation.status_code == 200, attestation.text
    payload = attestation.json()
    assert payload["store_counts"]["dataset_catalog"] >= 1
    assert payload["store_counts"]["connector_runs"] >= 1
    assert payload["store_counts"]["drift_baselines"] >= 1
    assert payload["store_counts"]["pipeline_runs"] >= 1
    assert payload["store_counts"]["ontology_snapshots"] >= 1
    assert payload["store_counts"]["recipe_registry"] >= 1

    proof = client.get("/v1/proof/bundle")
    assert proof.status_code == 200, proof.text
    proof_payload = proof.json()
    assert proof_payload["route_count"] >= 40
    assert proof_payload["verification_artifact_count"] >= 1
    assert "recipe_registry" in proof_payload["supported_lanes"]
    assert "s3_parquet" in proof_payload["connector_kinds"]

    readiness = client.get("/v1/readiness/report")
    assert readiness.status_code == 200, readiness.text
    readiness_payload = readiness.json()
    assert "s3_parquet" in readiness_payload["connector_kinds"]
    assert any(item["name"] == "connector_coverage" for item in readiness_payload["checks"])
    assert any(item["area"] == "cloud credentials" for item in readiness_payload["boundaries"])

    print("ACCEPTANCE_SPINE_OK")


if __name__ == "__main__":
    main()
