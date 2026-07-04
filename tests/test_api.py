import base64
import json
import math

from starlette.testclient import TestClient

from advanced_multimodal_ai.api import create_app
from advanced_multimodal_ai.execution_journal import (
    finish_script_execution,
    script_execution_window,
)

client = TestClient(create_app())


def _decode_ledger_payload(encoded: str) -> dict:
    padding = "=" * (-len(encoded) % 4)
    raw = base64.urlsafe_b64decode((encoded + padding).encode("ascii"))
    return json.loads(raw.decode("utf-8"))


def _assert_ledger_headers(response, *, route: str, method: str, status_code: int, scope: str):
    assert response.headers["x-amai-ledger-token"]
    assert response.headers["x-amai-ledger-scope"] == scope
    assert response.headers["x-amai-ledger-openapi"]
    assert response.headers["x-amai-ledger-stores"]
    assert response.headers["x-amai-ledger-payload"]
    payload = _decode_ledger_payload(response.headers["x-amai-ledger-payload"])
    assert payload["route"] == route
    assert payload["method"] == method
    assert payload["status_code"] == status_code
    assert payload["governance_scope"] == scope
    assert payload["governance_lanes"]


def _runtime_route_paths() -> set[str]:
    return {
        getattr(route, "path", "")
        for route in client.app.routes
        if getattr(route, "path", "").startswith("/v1/")
    }


def _music_feature_payload():
    return {
        "manifest": {
            "track_name": "Archive Choir Study",
            "owner": "tests",
            "source_uri": "s3://public-audio/archive-choir-study.wav",
            "source_kind": "s3_object",
            "content_sha256": "archive-choir-study-sha",
            "license_kind": "public_reference",
            "duration_ms": 18000,
            "sample_rate_hz": 16000,
            "channel_count": 1,
            "languages": ["en", "fil"],
            "regions": ["ph", "us"],
            "genres": ["choral", "signal-study"],
            "tags": ["music", "warehouse", "test"],
        },
        "partition_label": "test-reference",
        "dataset_name": "music_archive_choir_features",
        "dataset_version": "2026.07.03",
        "segments": [
            {
                "start_ms": 0,
                "end_ms": 6000,
                "label": "opening",
                "speaker": "section-a",
                "transcript_excerpt": "breath opens the phrase",
                "attributes": {
                    "transcript_ref": "line-001",
                    "speaker_or_section": "opening",
                    "frame_ref": "frame-001",
                    "video_window_start_ms": 120,
                    "video_window_end_ms": 5420,
                },
                "waveform": [round(0.64 * math.sin(index * 0.09), 6) for index in range(256)],
            },
            {
                "start_ms": 6000,
                "end_ms": 12000,
                "label": "lift",
                "speaker": "section-b",
                "transcript_excerpt": "the choir thickens",
                "attributes": {
                    "transcript_ref": "line-002",
                    "speaker_or_section": "lift",
                    "frame_ref": "frame-009",
                    "video_window_start_ms": 6240,
                    "video_window_end_ms": 11360,
                },
                "waveform": [
                    round(
                        (0.5 * math.sin(index * 0.12)) + (0.18 * math.cos(index * 0.04)),
                        6,
                    )
                    for index in range(256)
                ],
            },
            {
                "start_ms": 12000,
                "end_ms": 18000,
                "label": "resolve",
                "speaker": "section-c",
                "transcript_excerpt": "the phrase narrows again",
                "attributes": {
                    "transcript_ref": "line-003",
                    "speaker_or_section": "resolve",
                    "frame_ref": "frame-018",
                    "video_window_start_ms": 12160,
                    "video_window_end_ms": 17380,
                },
                "energy_trace": [round(0.32 + ((index % 24) / 100), 6) for index in range(128)],
            },
        ],
    }


def test_health_endpoint():
    response = client.get("/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "advanced-multimodal-ai"
    assert payload["status"] in {"ok", "degraded"}
    _assert_ledger_headers(
        response,
        route="/v1/health",
        method="GET",
        status_code=200,
        scope="runtime",
    )


def test_runtime_compliance_ledger_endpoint_surfaces_typed_governance_token():
    response = client.get(
        "/v1/runtime/compliance-ledger",
        params={"route": "/v1/catalog/register", "method": "POST", "status_code": 201},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["route"] == "/v1/catalog/register"
    assert payload["method"] == "POST"
    assert payload["status_code"] == 201
    assert payload["governance_scope"] == "catalog"
    assert "dataset_catalog" in payload["governance_lanes"]
    _assert_ledger_headers(
        response,
        route="/v1/runtime/compliance-ledger",
        method="GET",
        status_code=200,
        scope="runtime",
    )


def test_tensor_intercept_surfaces_high_frequency_modalities():
    response = client.post(
        "/v1/data/intercept",
        json={
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "embedding",
            "modalities": {
                "image": {
                    "shape": [1, 16],
                    "values": [
                        -1.0,
                        1.0,
                        -0.95,
                        0.95,
                        -1.0,
                        1.0,
                        -0.92,
                        0.92,
                        -1.0,
                        1.0,
                        -0.95,
                        0.95,
                        -1.0,
                        1.0,
                        -0.9,
                        0.9,
                    ],
                }
            },
            "metadata": {
                "restricted_modalities": ["image"],
                "max_intercept_risk": 0.55,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["policy_mode"] == "enforce"
    assert payload["triggered_modalities"] == ["image"]
    assert payload["intercept_profiles"][0]["status"] == "fail"
    assert payload["intercept_profiles"][0]["spatial_frequency"] >= 0.45


def test_infer_blocks_when_tensor_intercept_is_enforced():
    response = client.post(
        "/v1/infer",
        json={
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "embedding",
            "modalities": {
                "image": {
                    "shape": [1, 16],
                    "values": [
                        -1.0,
                        1.0,
                        -0.95,
                        0.95,
                        -1.0,
                        1.0,
                        -0.92,
                        0.92,
                        -1.0,
                        1.0,
                        -0.95,
                        0.95,
                        -1.0,
                        1.0,
                        -0.9,
                        0.9,
                    ],
                }
            },
            "metadata": {
                "restricted_modalities": ["image"],
                "block_tensor_intercept": True,
                "max_intercept_risk": 0.55,
            },
        },
    )
    assert response.status_code == 422
    payload = response.json()["detail"]
    assert payload["blocked"] is True
    assert payload["triggered_modalities"] == ["image"]
    _assert_ledger_headers(
        response,
        route="/v1/infer",
        method="POST",
        status_code=422,
        scope="inference",
    )


def test_runtime_attestation_reports_artifacts_and_store_counts():
    response = client.get("/v1/runtime/attestation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "advanced-multimodal-ai"
    assert "openapi_sha256" in payload
    assert "async_jobs" in payload["store_counts"]
    assert "recipe_registry" in payload["store_counts"]
    assert "lifecycle_policies" in payload["store_counts"]
    assert "change_controls" in payload["store_counts"]
    assert "supply_chain_snapshots" in payload["store_counts"]
    assert "execution_journal_runs" in payload["store_counts"]
    assert payload["verification_artifacts"]
    assert any(item["name"] == "Runtime schema" for item in payload["verification_artifacts"])


def test_edge_gateway_risk_score_stays_inside_declared_contract():
    response = client.post(
        "/v1/edge/evaluate",
        json={
            "jurisdiction": "EU_EEA",
            "source_region": "DE",
            "target_region": "DE",
            "connector_kind": "s3_parquet",
            "encrypted_in_transit": True,
            "modalities": {
                "audio": {
                    "shape": [1, 16],
                    "values": [
                        -1.0,
                        1.0,
                        -0.95,
                        0.95,
                        -0.9,
                        0.9,
                        -0.85,
                        0.85,
                        -1.0,
                        1.0,
                        -0.95,
                        0.95,
                        -0.9,
                        0.9,
                        -0.85,
                        0.85,
                    ],
                },
                "text": {
                    "shape": [1, 8],
                    "values": [0.11, 0.23, 0.17, 0.29, 0.13, 0.31, 0.19, 0.27],
                },
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert 0.0 <= payload["highest_modality_risk"] <= 1.0
    assert payload["route_action"] in {"hold", "route"}
    assert payload["metrics"]


def test_runtime_proof_bundle_reports_routes_tests_and_connector_kinds():
    response = client.get("/v1/proof/bundle")
    assert response.status_code == 200
    payload = response.json()
    assert payload["route_count"] >= 40
    assert payload["test_count"] >= 1
    assert "local_csv" in payload["connector_kinds"]
    assert "local_parquet" in payload["connector_kinds"]
    assert "s3_parquet" in payload["connector_kinds"]
    assert "web_html" in payload["connector_kinds"]
    assert any(item["label"] == "acceptance" for item in payload["verification_commands"])
    assert any(item["label"] == "readiness" for item in payload["verification_commands"])


def test_runtime_readiness_report_surfaces_limits_and_live_checks():
    response = client.get("/v1/readiness/report")
    assert response.status_code == 200
    payload = response.json()
    assert payload["route_count"] >= 40
    assert payload["test_count"] >= 1
    assert "s3_parquet" in payload["connector_kinds"]
    assert "web_html" in payload["connector_kinds"]
    assert payload["checks"]
    assert payload["boundaries"]
    check_names = {item["name"] for item in payload["checks"]}
    assert "connector_coverage" in check_names
    assert "recipe_resolution" in check_names
    assert "stewardship_surface" in check_names
    assert "execution_history" in check_names
    assert any(boundary["area"] == "cloud credentials" for boundary in payload["boundaries"])
    assert any(boundary["area"] == "public web intake" for boundary in payload["boundaries"])


def test_research_surfaces_explain_models_findings_and_connections():
    response = client.get("/v1/research/surfaces")
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["model_count"] >= 4
    assert payload["summary"]["open_question_count"] >= 1
    assert any(
        item["lane_id"] == "runtime_backend" and "/v1/research/surfaces" in item["entry_surfaces"]
        for item in payload["lanes"]
    )
    assert any(
        item["model_id"] == "adaptive_transformer" and item["improvement_paths"]
        for item in payload["model_cards"]
    )
    assert any(item["finding_id"] == "connector-spine-is-real" for item in payload["findings"])
    assert any(item["connection_id"] == "rows-to-batches" for item in payload["connections"])

    model_response = client.get("/v1/research/models")
    assert model_response.status_code == 200
    assert any(item["model_id"] == "complete_multimodal" for item in model_response.json())


def test_research_cymatic_surface_stays_tied_to_runtime_proof():
    response = client.get("/v1/research/cymatic-surface")
    assert response.status_code == 200
    payload = response.json()
    assert payload["route_count"] >= 40
    assert payload["test_count"] >= 1
    assert payload["total_runs"] >= 1
    assert payload["music_feature_run_count"] >= 1
    assert payload["harmonic_bands"]
    assert payload["stages"]
    assert payload["continuation_links"]
    assert any(stage["trace_paths"] for stage in payload["stages"])
    assert any(stage["files"] for stage in payload["stages"])


def test_operator_surfaces_keep_commands_skills_plugins_and_speech_tasks_together():
    response = client.get("/v1/operators/surfaces")
    assert response.status_code == 200
    payload = response.json()
    assert payload["route_count"] >= 40
    assert payload["command_count"] >= 6
    assert payload["skill_count"] >= 6
    assert payload["plugin_count"] >= 5
    assert payload["speech_task_count"] >= 5
    assert any(item["command_id"] == "music-feature-extract" for item in payload["commands"])
    assert any(item["skill_id"] == "inspect-plan-run-verify" for item in payload["skills"])
    assert any(item["plugin_id"] == "recursive-improvement-seam" for item in payload["plugins"])
    assert any(item["task_id"] == "caption-alignment-trace" for item in payload["speech_tasks"])
    assert any(item["metric_id"] == "music-runs" for item in payload["metrics"])

    speech_response = client.get("/v1/operators/speech-tasks")
    assert speech_response.status_code == 200
    assert any(item["task_id"] == "silence-padding-audit" for item in speech_response.json())


def test_music_warehouse_endpoints_persist_segments_embeddings_and_receipts():
    response = client.post("/v1/music/features/extract", json=_music_feature_payload())
    assert response.status_code == 200
    payload = response.json()
    assert payload["segment_count"] == 3
    assert payload["embedding_record_count"] == 3
    assert len(payload["embeddings"]) == 3
    assert len(payload["segment_index"]) == 3
    assert len(payload["receipts"]) == 2
    assert payload["feature_table_path"].endswith(".parquet")
    assert payload["embedding_table_path"].endswith(".parquet")

    overview = client.get("/v1/music/overview")
    assert overview.status_code == 200
    overview_payload = overview.json()
    assert overview_payload["manifest_count"] >= 1
    assert overview_payload["feature_run_count"] >= 1
    assert overview_payload["total_segments"] >= 3

    feature_rows = client.get("/v1/music/features/query", params={"run_id": payload["run_id"]})
    assert feature_rows.status_code == 200
    feature_rows_payload = feature_rows.json()
    assert feature_rows_payload["row_count"] >= 3
    assert feature_rows_payload["rows"]

    segments = client.get("/v1/music/segments", params={"run_id": payload["run_id"]})
    assert segments.status_code == 200
    segment_payload = segments.json()
    assert len(segment_payload) == 3
    assert any("missing-visual-link" not in item["quality_flags"] for item in segment_payload)

    alignment = client.get("/v1/music/alignment", params={"run_id": payload["run_id"]})
    assert alignment.status_code == 200
    alignment_payload = alignment.json()
    assert alignment_payload["windows"]
    assert any("audio" in item["modalities"] for item in alignment_payload["windows"])
    assert any("text" in item["modalities"] for item in alignment_payload["windows"])


def test_music_snapshot_surfaces_drift_and_change_proof():
    drift = client.get("/v1/music/drift")
    assert drift.status_code == 200
    drift_payload = drift.json()
    assert drift_payload["feature_run_count"] >= 1
    assert drift_payload["indicators"]
    assert any(
        item["indicator_id"] == "language-share-drift" for item in drift_payload["indicators"]
    )

    change = client.get("/v1/music/proof/change-report")
    assert change.status_code == 200
    change_payload = change.json()
    assert change_payload["feature_run_count"] >= 1
    assert change_payload["changes"]
    assert change_payload["changes"][0]["receipts"]

    snapshot = client.get("/v1/music/snapshot")
    assert snapshot.status_code == 200
    snapshot_payload = snapshot.json()
    assert snapshot_payload["overview"]["feature_run_count"] >= 1
    assert snapshot_payload["drift"]["indicators"]
    assert snapshot_payload["change_proof"]["changes"]
    assert snapshot_payload["segment_slice"]["rows"]


def test_industry_profiles_surface_shows_domain_transfer_without_leaving_runtime_truth():
    response = client.get("/v1/industries/profiles")
    assert response.status_code == 200
    payload = response.json()
    runtime_routes = _runtime_route_paths()
    assert payload["profile_count"] >= 10
    assert payload["continuation_links"]
    assert any(item["profile_id"] == "healthcare" for item in payload["profiles"])
    assert any(item["profile_id"] == "supply_chain" for item in payload["profiles"])
    for profile in payload["profiles"]:
        assert profile["anchor_routes"]
        assert set(profile["anchor_routes"]).issubset(runtime_routes)

    media_profile = next(item for item in payload["profiles"] if item["profile_id"] == "media")
    assert "audio" in media_profile["primary_modalities"]
    assert "/v1/music/features/extract" in media_profile["anchor_routes"]
    assert media_profile["proof_surfaces"]

    healthcare_profile = next(
        item for item in payload["profiles"] if item["profile_id"] == "healthcare"
    )
    assert "/v1/ontology/liability" in healthcare_profile["anchor_routes"]
    assert healthcare_profile["strict_checks"]


def test_industrial_scenarios_surface_lists_machine_families_and_expected_faults():
    response = client.get("/v1/industrial/scenarios")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["scenarios"]) >= 3
    assert any(
        item["scenario_id"] == "diesel-engine-overheat-window" for item in payload["scenarios"]
    )
    assert any(item["asset_kind"] == "hydraulic_system" for item in payload["scenarios"])


def test_industrial_diagnose_builds_deterministic_diagnosis_compliance_and_proof_chain():
    response = client.post(
        "/v1/industrial/diagnose",
        json={
            "asset_kind": "diesel_engine",
            "machine_family": "field-diagnostics-reference",
            "technician_report": "Repeated stall under load with smoke pulse and metallic knock.",
            "sensors": [
                {"sensor_id": "oil_pressure_kpa", "value": 112.0, "unit": "kPa"},
                {"sensor_id": "coolant_temp_c", "value": 108.4, "unit": "C"},
                {"sensor_id": "boost_pressure_kpa", "value": 101.0, "unit": "kPa"},
                {"sensor_id": "exhaust_opacity_pct", "value": 74.0, "unit": "%"},
            ],
            "observations": [
                {"component": "engine", "symptom": "stall", "detail": "stall under load"},
                {"component": "exhaust", "symptom": "smoke", "detail": "dark smoke pulse"},
            ],
            "work_context": {
                "lockout_applied": False,
                "energy_isolated": False,
                "guard_interlock_verified": True,
                "emergency_stop_verified": True,
                "manual_reset_verified": False,
                "restart_requested": True,
                "safety_function_proof_test_overdue": True,
                "diagnostic_coverage_percent": 86.0,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["verdict"] == "block"
    assert any(
        item["diagnosis_id"] == "diesel-lubrication-collapse" for item in payload["diagnoses"]
    )
    assert any(item["standard"] == "OSHA 1910" for item in payload["compliance_findings"])
    assert any(
        item["invariant_id"] == "lockout-before-intervention" for item in payload["invariants"]
    )
    assert payload["fault_graph"]["nodes"]
    assert payload["fault_graph"]["edges"]
    assert any(
        item["node_id"] == "diagnosis:diesel-lubrication-collapse"
        for item in payload["fault_graph"]["nodes"]
    )
    assert any(
        item["source"] == "sensor:oil_pressure_kpa"
        and item["target"] == "diagnosis:diesel-lubrication-collapse"
        for item in payload["fault_graph"]["edges"]
    )
    assert payload["proof_tree"]
    assert payload["audit_trail"]
    assert payload["formal_trace"]


def test_industrial_model_check_blocks_restart_outside_protective_state():
    response = client.post(
        "/v1/industrial/model-check",
        json={
            "work_context": {
                "lockout_applied": True,
                "energy_isolated": True,
                "guard_interlock_verified": False,
                "emergency_stop_verified": True,
                "manual_reset_verified": False,
                "restart_requested": True,
            },
            "compliance_findings": [
                {
                    "standard": "ISO 13849-1",
                    "clause": "6.2.6",
                    "status": "block",
                    "requirement": "The protective guard path must be verified before restart.",
                    "evidence": ["guard_interlock_verified=False"],
                    "implication": "Restart remains blocked.",
                }
            ],
            "trace": [
                {
                    "from_state": "observe",
                    "to_state": "isolate",
                    "command": "stabilize machine boundary",
                    "lockout_applied": True,
                    "energy_isolated": True,
                    "guard_interlock_verified": False,
                    "emergency_stop_verified": True,
                    "manual_reset_verified": False,
                },
                {
                    "from_state": "isolate",
                    "to_state": "restart",
                    "command": "attempt restart too early",
                    "lockout_applied": True,
                    "energy_isolated": True,
                    "guard_interlock_verified": False,
                    "emergency_stop_verified": True,
                    "manual_reset_verified": False,
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["allowed"] is False
    assert payload["blocked_transitions"]
    assert any(
        item["invariant_id"] == "regulatory-blocks-stop-restart" for item in payload["invariants"]
    )


def test_repository_pulse_tracks_lane_health_and_artifacts():
    response = client.get("/v1/repository/pulse")
    assert response.status_code == 200
    payload = response.json()
    assert payload["route_count"] >= 40
    assert payload["test_count"] >= 1
    assert any(
        item["lane_id"] == "generated_clients" and item["live_score"] >= 50
        for item in payload["lanes"]
    )
    assert any(item["lane_id"] == "execution_history" for item in payload["lanes"])
    assert any(
        artifact["path"] == "openapi/openapi.json"
        for lane in payload["lanes"]
        for artifact in lane["artifacts"]
    )
    assert any(item["lane_id"] == "benchmark_lane" for item in payload["lanes"])


def test_repository_growth_snapshot_stays_grounded_in_live_repo_signals():
    response = client.get("/v1/growth/snapshot")
    assert response.status_code == 200
    payload = response.json()
    assert payload["repository"] == "Cazzy-Aporbo/Advanced_multi-modal-AI"
    assert payload["route_count"] >= 40
    assert payload["test_count"] >= 1
    assert payload["public_surface_count"] >= 8
    assert payload["proof_export_count"] >= 1
    assert payload["docs_count"] >= 1
    assert payload["notebook_count"] == 0
    assert "README.md" not in payload["community_files"]


def test_reference_benchmark_runs_pipeline_replay_and_proof_lanes():
    response = client.get("/v1/benchmarks/reference")
    assert response.status_code == 200
    payload = response.json()
    assert payload["stage_count"] >= 6
    assert payload["pipeline_run_id"]
    assert payload["replay_frame_count"] >= 1
    assert payload["replay_verified"] is True
    assert any(stage["stage_id"] == "pipeline_replay" for stage in payload["stages"])
    replay_stage = next(
        stage for stage in payload["stages"] if stage["stage_id"] == "pipeline_replay"
    )
    assert replay_stage["status"] == "pass"
    assert any("Frame parity: verified." in note for note in replay_stage["notes"])


def test_execution_journal_lists_persisted_script_runs():
    started_at, start_counter = script_execution_window()
    finish_script_execution(
        lane="test_export_lane",
        command="python3 scripts/test_export_lane.py",
        artifacts=[("README.md", "Repository overview file.")],
        started_at=started_at,
        start_counter=start_counter,
        status="pass",
        notes=["journal route test"],
    )

    response = client.get("/v1/execution/journal", params={"limit": 10})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_runs"] >= 1
    assert "test_export_lane" in payload["lane_counts"]
    assert any(
        item["lane"] == "test_export_lane" and item["status"] == "pass"
        for item in payload["recent_runs"]
    )


def test_dataset_catalog_registration_and_evolution_report():
    register = client.post(
        "/v1/catalog/register",
        json={
            "dataset_name": "music_event_log",
            "owner": "cazandra",
            "version": "2026.07.02",
            "modality": "tabular",
            "partition_keys": ["event_date"],
            "primary_keys": ["event_id"],
            "fields": [
                {"name": "event_id", "dtype": "string", "nullable": False},
                {"name": "event_date", "dtype": "date", "nullable": False},
                {"name": "artist_id", "dtype": "string", "nullable": False},
            ],
            "tags": ["events", "music"],
        },
    )
    assert register.status_code == 200
    payload = register.json()
    assert payload["fingerprint"]
    assert "dataset=music_event_log" in payload["canonical_schema"]

    listed = client.get("/v1/catalog/datasets")
    assert listed.status_code == 200
    assert any(item["dataset_name"] == "music_event_log" for item in listed.json())

    evolution = client.post(
        "/v1/catalog/evolution",
        json={
            "dataset_name": "music_event_log",
            "candidate_version": "2026.07.03",
            "fields": [
                {"name": "event_id", "dtype": "string", "nullable": False},
                {"name": "event_date", "dtype": "timestamp", "nullable": False},
                {"name": "artist_id", "dtype": "string", "nullable": False},
                {"name": "genre_id", "dtype": "string", "nullable": True},
            ],
        },
    )
    assert evolution.status_code == 200
    evolution_payload = evolution.json()
    assert evolution_payload["compatible"] is False
    assert evolution_payload["breaking_changes"]
    assert any(
        item["change_type"] == "dtype_changed" for item in evolution_payload["breaking_changes"]
    )
    assert any(item["change_type"] == "added" for item in evolution_payload["additive_changes"])


def test_stewardship_surfaces_track_lifecycle_change_control_and_supply_chain():
    dataset_response = client.post(
        "/v1/catalog/register",
        json={
            "dataset_name": "music_distribution_tail",
            "owner": "cazandra",
            "version": "2026.07.02",
            "modality": "tabular",
            "partition_keys": ["market"],
            "primary_keys": ["observation_id"],
            "fields": [
                {"name": "observation_id", "dtype": "string", "nullable": False},
                {"name": "market", "dtype": "string", "nullable": False},
                {"name": "attention_score", "dtype": "float", "nullable": False},
            ],
            "tags": ["market", "music"],
        },
    )
    assert dataset_response.status_code == 200
    dataset_payload = dataset_response.json()

    lifecycle = client.post(
        "/v1/stewardship/lifecycle",
        json={
            "dataset_name": "music_distribution_tail",
            "owner": "cazandra",
            "data_classification": "regulated",
            "residency_regions": ["eu-west-1", "ap-southeast-1"],
            "allowed_uses": ["analysis", "retrieval_review"],
            "effective_from": "2020-01-01T00:00:00+00:00",
            "retention_days": 365,
            "half_life_days": 120,
            "review_interval_days": 30,
            "removal_mode": "anonymize",
            "evidence_refs": ["contract://music-distribution-tail-v1"],
        },
    )
    assert lifecycle.status_code == 200
    lifecycle_payload = lifecycle.json()
    assert lifecycle_payload["dataset_id"] == dataset_payload["dataset_id"]
    assert lifecycle_payload["state"] == "removal_due"

    listed_lifecycle = client.get("/v1/stewardship/lifecycle")
    assert listed_lifecycle.status_code == 200
    assert any(
        item["policy_id"] == lifecycle_payload["policy_id"] for item in listed_lifecycle.json()
    )

    change_control = client.post(
        "/v1/stewardship/change-controls",
        json={
            "title": "Rotate market export route",
            "owner": "cazandra",
            "change_kind": "connector",
            "severity": "high",
            "status": "approved",
            "summary": "Move the export lane behind a narrower regional review path.",
            "affected_datasets": ["music_distribution_tail"],
            "affected_connectors": ["s3_parquet"],
            "affected_routes": ["/v1/connectors/pipeline-ingest"],
            "linked_policy_ids": [lifecycle_payload["policy_id"]],
            "validation_commands": ["pytest -q tests/test_api.py -k stewardship"],
            "rollback_notes": ["Restore the prior connector only after lineage review."],
        },
    )
    assert change_control.status_code == 200
    change_payload = change_control.json()
    assert change_payload["status"] == "approved"

    snapshot = client.post(
        "/v1/stewardship/supply-chain",
        json={
            "label": "music-tail-lane",
            "owner": "cazandra",
            "tenant_id": "advanced-multimodal-music",
            "nodes": [
                {
                    "node_id": "src-node",
                    "label": "S3 parquet intake",
                    "node_kind": "connector",
                },
                {
                    "node_id": "dataset-node",
                    "label": "Music distribution tail",
                    "node_kind": "dataset",
                    "dataset_name": "music_distribution_tail",
                },
                {
                    "node_id": "consumer-node",
                    "label": "Regional analyst workspace",
                    "node_kind": "consumer",
                },
            ],
            "edges": [
                {
                    "from_node_id": "src-node",
                    "to_node_id": "dataset-node",
                    "movement": "ingest",
                    "carries_data_categories": ["market_signals"],
                    "governed": True,
                    "deletion_supported": True,
                },
                {
                    "from_node_id": "dataset-node",
                    "to_node_id": "consumer-node",
                    "movement": "export",
                    "carries_data_categories": ["market_signals"],
                    "cross_border": True,
                    "governed": False,
                    "deletion_supported": False,
                },
            ],
        },
    )
    assert snapshot.status_code == 200
    snapshot_payload = snapshot.json()
    assert snapshot_payload["cross_border_edge_count"] == 1
    assert snapshot_payload["ungoverned_edge_count"] == 1

    posture = client.get("/v1/stewardship/posture")
    assert posture.status_code == 200
    posture_payload = posture.json()
    assert posture_payload["policy_count"] >= 1
    assert posture_payload["approved_change_controls"] >= 1
    assert posture_payload["cross_border_edge_count"] >= 1
    assert any(
        item["dataset_name"] == "music_distribution_tail" and item["has_policy"]
        for item in posture_payload["datasets"]
    )


def test_local_csv_connector_registers_dataset_and_feeds_pipeline(tmp_path):
    csv_path = tmp_path / "music_signal.csv"
    csv_path.write_text(
        "\n".join(
            [
                "event_id,event_date,sensor_a,sensor_b,sensor_c,tab_a,tab_b,tab_c",
                "evt-1,2026-07-01,0.1,0.2,0.3,1.0,0.9,0.8",
                "evt-2,2026-07-02,0.2,0.3,0.4,0.9,0.8,0.7",
                "evt-3,2026-07-03,0.3,0.4,0.5,0.8,0.7,0.6",
            ]
        ),
        encoding="utf-8",
    )

    registration = client.post(
        "/v1/connectors/register",
        json={
            "connector": {"kind": "local_csv", "source": str(csv_path)},
            "dataset_name": "music_signal_rows",
            "owner": "cazandra",
            "version": "2026.07.02",
            "partition_keys": ["event_date"],
            "primary_keys": ["event_id"],
            "tags": ["music", "signals"],
        },
    )
    assert registration.status_code == 200
    registration_payload = registration.json()
    assert registration_payload["record_count"] == 3
    assert registration_payload["benchmark"]["rows_per_second"] > 0.0
    assert any(field["name"] == "sensor_a" for field in registration_payload["dataset"]["fields"])

    baseline_request = {
        "label": "connector-cohort-001",
        "request": {
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "embedding",
            "metadata": {"request_id": "baseline-connector-001"},
            "modalities": {
                "tabular": {
                    "shape": [3, 3],
                    "values": [1.0, 0.9, 0.8, 0.9, 0.8, 0.7, 0.8, 0.7, 0.6],
                },
                "sensor": {
                    "shape": [3, 3],
                    "values": [0.1, 0.2, 0.3, 0.2, 0.3, 0.4, 0.3, 0.4, 0.5],
                },
            },
        },
    }
    assert client.post("/v1/drift/baselines", json=baseline_request).status_code == 200

    ingest = client.post(
        "/v1/connectors/pipeline-ingest",
        json={
            "connector": {"kind": "local_csv", "source": str(csv_path)},
            "dataset_name": "music_signal_rows",
            "owner": "cazandra",
            "version": "2026.07.03",
            "stream_id": "connector-stream",
            "batch_label": "csv-window-01",
            "baseline_label": "connector-cohort-001",
            "modality_mappings": [
                {
                    "modality": "tabular",
                    "feature_fields": ["tab_a", "tab_b", "tab_c"],
                    "source": "table-feed",
                },
                {
                    "modality": "sensor",
                    "feature_fields": ["sensor_a", "sensor_b", "sensor_c"],
                    "source": "sensor-feed",
                },
            ],
            "partition_key_field": "event_date",
        },
    )
    assert ingest.status_code == 200
    ingest_payload = ingest.json()
    assert ingest_payload["connector_run"]["record_count"] == 3
    assert ingest_payload["pipeline_run"]["status"] == "accepted"
    assert ingest_payload["pipeline_run"]["paired_batch_size"] == 3
    assert ingest_payload["pipeline_run"]["modality_counts"]["tabular"] == 3
    assert ingest_payload["pipeline_run"]["modality_counts"]["sensor"] == 3

    run_id = ingest_payload["connector_run"]["run_id"]
    connector_run = client.get(f"/v1/connectors/runs/{run_id}")
    assert connector_run.status_code == 200
    assert connector_run.json()["pipeline_run_id"] == ingest_payload["pipeline_run"]["run_id"]


def test_recipe_compile_persists_manifest_and_resolves_catalog_sources():
    train_register = client.post(
        "/v1/catalog/register",
        json={
            "dataset_name": "vl_recipe_train",
            "owner": "cazandra",
            "version": "2026.07.02",
            "modality": "image",
            "partition_keys": ["capture_day"],
            "primary_keys": ["frame_id"],
            "fields": [
                {"name": "frame_id", "dtype": "string", "nullable": False},
                {"name": "capture_day", "dtype": "date", "nullable": False},
                {"name": "image_uri", "dtype": "string", "nullable": False},
                {"name": "caption", "dtype": "string", "nullable": True},
            ],
            "tags": ["vision", "train"],
        },
    )
    assert train_register.status_code == 200

    eval_register = client.post(
        "/v1/catalog/register",
        json={
            "dataset_name": "vl_recipe_eval",
            "owner": "cazandra",
            "version": "2026.07.02",
            "modality": "text",
            "partition_keys": ["capture_day"],
            "primary_keys": ["sample_id"],
            "fields": [
                {"name": "sample_id", "dtype": "string", "nullable": False},
                {"name": "capture_day", "dtype": "date", "nullable": False},
                {"name": "question", "dtype": "string", "nullable": False},
                {"name": "answer", "dtype": "string", "nullable": True},
            ],
            "tags": ["eval", "text"],
        },
    )
    assert eval_register.status_code == 200

    compiled = client.post(
        "/v1/recipes/compile",
        json={
            "label": "qwen-style-vl-recipe",
            "owner": "cazandra",
            "objective": "finetune",
            "model": {
                "model_ref": "Qwen/Qwen2.5-VL-7B-Instruct",
                "family": "vision-language",
                "context_length": 16384,
                "adapter_kind": "lora",
                "precision": "bf16",
                "freeze_vision_tower": True,
                "target_modules": ["attn.q_proj", "attn.v_proj"],
            },
            "sources": [
                {
                    "split": "train",
                    "modality": "image",
                    "dataset_name": "vl_recipe_train",
                    "dataset_version": "2026.07.02",
                    "expected_rows": 2400,
                },
                {
                    "split": "eval",
                    "modality": "text",
                    "dataset_name": "vl_recipe_eval",
                    "expected_rows": 480,
                },
            ],
            "training": {
                "epochs": 2.0,
                "micro_batch_size": 2,
                "gradient_accumulation_steps": 4,
                "learning_rate": 0.00002,
                "save_interval_steps": 250,
                "eval_interval_steps": 125,
            },
            "distributed": {
                "engine": "deepspeed",
                "node_count": 2,
                "devices_per_node": 4,
                "zero_stage": 3,
                "gradient_checkpointing": True,
                "offload_optimizer": False,
                "launcher_env": {"NCCL_DEBUG": "WARN"},
            },
            "evaluation": {
                "metrics": ["loss", "retrieval_recall_at_10"],
                "primary_metric": "retrieval_recall_at_10",
                "minimum_thresholds": {"retrieval_recall_at_10": 0.42},
                "holdout_split": 0.18,
            },
            "tags": ["vision-language", "recipe"],
        },
    )
    assert compiled.status_code == 200, compiled.text
    payload = compiled.json()
    assert payload["resolved_sources"][0]["resolved"] is True
    assert payload["resolved_sources"][1]["resolved"] is True
    assert payload["launch_profile"]["launcher"] == "torchrun"
    assert payload["launch_profile"]["engine"] == "deepspeed"
    assert payload["launch_profile"]["estimated_global_batch_size"] == 64
    assert any(
        command["label"] == "export_manifest" and command["verified"]
        for command in payload["launch_profile"]["verified_commands"]
    )
    assert payload["launch_profile"]["launcher_template"].startswith(
        "torchrun --nnodes 2 --nproc_per_node 4"
    )

    recipe_id = payload["recipe_id"]
    listed = client.get("/v1/recipes")
    assert listed.status_code == 200
    assert any(item["recipe_id"] == recipe_id for item in listed.json())

    fetched = client.get(f"/v1/recipes/{recipe_id}")
    assert fetched.status_code == 200
    assert fetched.json()["recipe_id"] == recipe_id
    assert fetched.json()["evaluation"]["primary_metric"] == "retrieval_recall_at_10"


def test_local_parquet_connector_registers_dataset_and_feeds_pipeline(tmp_path):
    import pyarrow as pa
    import pyarrow.parquet as pq

    parquet_path = tmp_path / "music_signal.parquet"
    table = pa.table(
        {
            "event_id": ["evt-11", "evt-12", "evt-13"],
            "event_date": ["2026-07-11", "2026-07-12", "2026-07-13"],
            "sensor_a": [0.11, 0.22, 0.33],
            "sensor_b": [0.21, 0.32, 0.43],
            "tab_a": [0.91, 0.81, 0.71],
            "tab_b": [0.88, 0.78, 0.68],
        }
    )
    pq.write_table(table, parquet_path)

    registration = client.post(
        "/v1/connectors/register",
        json={
            "connector": {"kind": "local_parquet", "source": str(parquet_path)},
            "dataset_name": "music_signal_parquet",
            "owner": "cazandra",
            "version": "2026.07.11",
            "partition_keys": ["event_date"],
            "primary_keys": ["event_id"],
            "tags": ["music", "parquet"],
        },
    )
    assert registration.status_code == 200, registration.text
    registration_payload = registration.json()
    assert registration_payload["record_count"] == 3
    assert registration_payload["benchmark"]["rows_per_second"] > 0.0
    assert any(field["name"] == "sensor_a" for field in registration_payload["dataset"]["fields"])

    baseline_request = {
        "label": "connector-parquet-cohort-001",
        "request": {
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "embedding",
            "metadata": {"request_id": "baseline-parquet-001"},
            "modalities": {
                "tabular": {
                    "shape": [3, 2],
                    "values": [0.91, 0.88, 0.81, 0.78, 0.71, 0.68],
                },
                "sensor": {
                    "shape": [3, 2],
                    "values": [0.11, 0.21, 0.22, 0.32, 0.33, 0.43],
                },
            },
        },
    }
    assert client.post("/v1/drift/baselines", json=baseline_request).status_code == 200

    ingest = client.post(
        "/v1/connectors/pipeline-ingest",
        json={
            "connector": {"kind": "local_parquet", "source": str(parquet_path)},
            "dataset_name": "music_signal_parquet",
            "owner": "cazandra",
            "version": "2026.07.12",
            "stream_id": "connector-parquet-stream",
            "batch_label": "parquet-window-01",
            "baseline_label": "connector-parquet-cohort-001",
            "modality_mappings": [
                {
                    "modality": "tabular",
                    "feature_fields": ["tab_a", "tab_b"],
                    "source": "parquet-table",
                },
                {
                    "modality": "sensor",
                    "feature_fields": ["sensor_a", "sensor_b"],
                    "source": "parquet-sensor",
                },
            ],
            "partition_key_field": "event_date",
        },
    )
    assert ingest.status_code == 200, ingest.text
    ingest_payload = ingest.json()
    assert ingest_payload["connector_run"]["record_count"] == 3
    assert ingest_payload["connector_run"]["connector_kind"] == "local_parquet"
    assert ingest_payload["pipeline_run"]["status"] == "accepted"
    assert ingest_payload["pipeline_run"]["paired_batch_size"] == 3


def test_s3_parquet_connector_registers_dataset_and_feeds_pipeline(monkeypatch):
    import pyarrow as pa
    import pyarrow.parquet as pq

    from advanced_multimodal_ai import connectors as connector_module

    output = pa.BufferOutputStream()
    table = pa.table(
        {
            "event_id": ["evt-21", "evt-22", "evt-23"],
            "event_date": ["2026-07-21", "2026-07-22", "2026-07-23"],
            "sensor_a": [0.14, 0.24, 0.34],
            "sensor_b": [0.18, 0.28, 0.38],
            "tab_a": [0.94, 0.84, 0.74],
            "tab_b": [0.89, 0.79, 0.69],
        }
    )
    pq.write_table(table, output)
    parquet_bytes = output.getvalue().to_pybytes()

    captured: dict[str, object] = {}

    class FakeBody:
        def read(self) -> bytes:
            return parquet_bytes

    class FakeS3Client:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def get_object(self, *, Bucket: str, Key: str):
            captured["bucket"] = Bucket
            captured["key"] = Key
            return {"Body": FakeBody()}

    class FakeBoto3:
        def client(self, service_name: str, **kwargs):
            assert service_name == "s3"
            return FakeS3Client(**kwargs)

    monkeypatch.setattr(connector_module, "boto3", FakeBoto3())
    monkeypatch.setenv("AMAI_AWS_ACCESS_KEY_ID", "access-test")
    monkeypatch.setenv("AMAI_AWS_SECRET_ACCESS_KEY", "secret-test")

    registration = client.post(
        "/v1/connectors/register",
        json={
            "connector": {
                "kind": "s3_parquet",
                "source": "s3://advanced-multimodal-proof/music_signal.parquet",
                "region": "us-east-1",
                "endpoint_url": "https://object.example.invalid",
                "secret_env": {
                    "aws_access_key_id": "AMAI_AWS_ACCESS_KEY_ID",
                    "aws_secret_access_key": "AMAI_AWS_SECRET_ACCESS_KEY",
                },
            },
            "dataset_name": "music_signal_s3",
            "owner": "cazandra",
            "version": "2026.07.21",
            "partition_keys": ["event_date"],
            "primary_keys": ["event_id"],
            "tags": ["music", "s3", "parquet"],
        },
    )
    assert registration.status_code == 200, registration.text
    registration_payload = registration.json()
    assert registration_payload["record_count"] == 3
    assert registration_payload["benchmark"]["rows_per_second"] > 0.0
    assert captured["bucket"] == "advanced-multimodal-proof"
    assert captured["key"] == "music_signal.parquet"
    assert captured["region_name"] == "us-east-1"
    assert captured["endpoint_url"] == "https://object.example.invalid"
    assert captured["aws_access_key_id"] == "access-test"
    assert captured["aws_secret_access_key"] == "secret-test"

    baseline_request = {
        "label": "connector-s3-cohort-001",
        "request": {
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "embedding",
            "metadata": {"request_id": "baseline-s3-001"},
            "modalities": {
                "tabular": {
                    "shape": [3, 2],
                    "values": [0.94, 0.89, 0.84, 0.79, 0.74, 0.69],
                },
                "sensor": {
                    "shape": [3, 2],
                    "values": [0.14, 0.18, 0.24, 0.28, 0.34, 0.38],
                },
            },
        },
    }
    assert client.post("/v1/drift/baselines", json=baseline_request).status_code == 200

    ingest = client.post(
        "/v1/connectors/pipeline-ingest",
        json={
            "connector": {
                "kind": "s3_parquet",
                "source": "s3://advanced-multimodal-proof/music_signal.parquet",
                "region": "us-east-1",
                "endpoint_url": "https://object.example.invalid",
                "secret_env": {
                    "aws_access_key_id": "AMAI_AWS_ACCESS_KEY_ID",
                    "aws_secret_access_key": "AMAI_AWS_SECRET_ACCESS_KEY",
                },
            },
            "dataset_name": "music_signal_s3",
            "owner": "cazandra",
            "version": "2026.07.22",
            "stream_id": "connector-s3-stream",
            "batch_label": "s3-window-01",
            "baseline_label": "connector-s3-cohort-001",
            "modality_mappings": [
                {
                    "modality": "tabular",
                    "feature_fields": ["tab_a", "tab_b"],
                    "source": "s3-table",
                },
                {
                    "modality": "sensor",
                    "feature_fields": ["sensor_a", "sensor_b"],
                    "source": "s3-sensor",
                },
            ],
            "partition_key_field": "event_date",
        },
    )
    assert ingest.status_code == 200, ingest.text
    ingest_payload = ingest.json()
    assert ingest_payload["connector_run"]["record_count"] == 3
    assert ingest_payload["connector_run"]["connector_kind"] == "s3_parquet"
    assert ingest_payload["pipeline_run"]["status"] == "accepted"
    assert ingest_payload["pipeline_run"]["paired_batch_size"] == 3


def test_inference_endpoint_returns_fused_embedding():
    response = client.post(
        "/v1/infer",
        json={
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "classification",
            "num_classes": 3,
            "modalities": {
                "text": {"shape": [2, 4], "values": [0.0, 0.5, 1.0, 1.5, -0.5, 0.25, 0.75, 1.25]},
                "audio": {"shape": [2, 4], "values": [1.0, 0.0, 0.5, 0.25, 0.5, 0.75, 1.0, 1.25]},
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["runtime_mode"] == "contract"
    assert "fused_embedding" in payload["outputs"]
    assert "class_probabilities" in payload["outputs"]


def test_data_profile_endpoint_reports_alignment_and_readiness():
    response = client.post(
        "/v1/data/profile",
        json={
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "embedding",
            "metadata": {"request_id": "profile-01"},
            "modalities": {
                "text": {"shape": [2, 4], "values": [0.0, 0.2, 0.4, 0.6, 0.1, 0.3, 0.5, 0.7]},
                "audio": {"shape": [2, 4], "values": [0.1, 0.2, 0.5, 0.8, 0.1, 0.4, 0.6, 0.9]},
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"] == "profile-01"
    assert len(payload["modality_profiles"]) == 2
    assert payload["fusion_readiness"] >= 0.0
    assert payload["pairwise_alignment"]


def test_bias_taxonomy_contains_sixty_categories():
    response = client.get("/v1/bias/taxonomy")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 60
    assert any(item["stage"] == "measurement" for item in payload)


def test_bias_assessment_maps_risk_to_active_system_stages():
    response = client.post(
        "/v1/bias/assess",
        json={
            "system_name": "comparative-multimodal-review",
            "active_stages": ["measurement", "retrieval", "governance"],
            "observed_signals": ["sensor", "drift", "ranking", "feedback"],
            "data_categories": ["biometric", "pii"],
            "notes": ["quality varies by source"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_categories"] == 60
    assert payload["findings"]
    assert "measurement" in payload["stage_summary"]
    assert any(item["severity"] in {"elevated", "critical"} for item in payload["findings"])


def test_data_provenance_endpoint_is_deterministic():
    request = {
        "model_id": "adaptive_transformer",
        "runtime_mode": "contract",
        "target": "embedding",
        "metadata": {"request_id": "receipt-01", "author": "Cazandra Aporbo"},
        "modalities": {
            "text": {"shape": [1, 4], "values": [0.2, 0.4, 0.6, 0.8]},
            "image": {"shape": [1, 4], "values": [0.8, 0.6, 0.4, 0.2]},
        },
    }
    first = client.post("/v1/data/provenance", json=request)
    second = client.post("/v1/data/provenance", json=request)
    assert first.status_code == 200
    assert second.status_code == 200
    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["payload_digest"] == second_payload["payload_digest"]
    assert first_payload["metadata_digest"] == second_payload["metadata_digest"]
    assert first_payload["modality_digests"] == second_payload["modality_digests"]


def test_alignment_windows_endpoint_groups_related_observations():
    response = client.post(
        "/v1/alignment/windows",
        json={
            "merge_gap_ms": 100,
            "minimum_modalities": 2,
            "observations": [
                {
                    "modality": "text",
                    "start_ms": 0,
                    "end_ms": 400,
                    "confidence": 0.9,
                    "source_id": "t1",
                },
                {
                    "modality": "audio",
                    "start_ms": 120,
                    "end_ms": 420,
                    "confidence": 0.8,
                    "source_id": "a1",
                },
                {
                    "modality": "image",
                    "start_ms": 900,
                    "end_ms": 1200,
                    "confidence": 0.85,
                    "source_id": "i1",
                },
                {
                    "modality": "audio",
                    "start_ms": 940,
                    "end_ms": 1180,
                    "confidence": 0.75,
                    "source_id": "a2",
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["windows"]) == 2
    assert payload["windows"][0]["modalities"] == ["audio", "text"]
    assert payload["modality_coverage_ms"]["audio"] > 0


def test_population_baseline_can_be_saved_and_listed():
    payload = {
        "label": "speech-cohort-001",
        "notes": ["Reviewed launch population for speech-first classification."],
        "request": {
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "embedding",
            "metadata": {"request_id": "baseline-001"},
            "modalities": {
                "text": {"shape": [2, 4], "values": [0.1, 0.2, 0.3, 0.4, 0.2, 0.3, 0.4, 0.5]},
                "audio": {"shape": [2, 4], "values": [0.2, 0.3, 0.4, 0.5, 0.3, 0.4, 0.5, 0.6]},
            },
        },
    }
    create_response = client.post("/v1/drift/baselines", json=payload)
    assert create_response.status_code == 200
    baseline = create_response.json()
    assert baseline["label"] == "speech-cohort-001"
    assert baseline["coverage_score"] > 0.0

    list_response = client.get("/v1/drift/baselines")
    assert list_response.status_code == 200
    labels = {record["label"] for record in list_response.json()}
    assert "speech-cohort-001" in labels


def test_population_drift_check_flags_sparse_shifted_population():
    baseline_request = {
        "label": "sensor-cohort-001",
        "request": {
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "embedding",
            "metadata": {"request_id": "baseline-002"},
            "modalities": {
                "sensor": {"shape": [2, 4], "values": [0.1, 0.3, 0.5, 0.7, 0.2, 0.4, 0.6, 0.8]},
                "tabular": {"shape": [2, 4], "values": [1.0, 0.9, 0.8, 0.7, 0.9, 0.8, 0.7, 0.6]},
            },
        },
    }
    assert client.post("/v1/drift/baselines", json=baseline_request).status_code == 200

    drift_response = client.post(
        "/v1/drift/check",
        json={
            "baseline_label": "sensor-cohort-001",
            "request": {
                "model_id": "adaptive_transformer",
                "runtime_mode": "contract",
                "target": "embedding",
                "metadata": {"request_id": "drift-002"},
                "modalities": {
                    "sensor": {"shape": [2, 4], "values": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
                    "tabular": {
                        "shape": [2, 4],
                        "values": [1.0, 1.0, 1.0, 1.0, 0.95, 1.0, 1.0, 1.0],
                    },
                },
            },
            "block_on_failure": True,
        },
    )
    assert drift_response.status_code == 200
    payload = drift_response.json()
    assert payload["baseline_label"] == "sensor-cohort-001"
    assert payload["blocked"] is True
    assert payload["drift_score"] > 0.4
    assert any(delta["status"] == "fail" for delta in payload["modality_deltas"])


def test_infer_endpoint_can_warn_or_block_on_population_drift():
    baseline_request = {
        "label": "video-cohort-001",
        "request": {
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "classification",
            "num_classes": 2,
            "metadata": {"request_id": "baseline-003"},
            "modalities": {
                "text": {"shape": [1, 4], "values": [0.2, 0.4, 0.6, 0.8]},
                "video": {"shape": [1, 4], "values": [0.8, 0.6, 0.4, 0.2]},
            },
        },
    }
    assert client.post("/v1/drift/baselines", json=baseline_request).status_code == 200

    warning_response = client.post(
        "/v1/infer",
        json={
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "classification",
            "num_classes": 2,
            "metadata": {
                "request_id": "warn-003",
                "population_baseline_label": "video-cohort-001",
                "block_population_drift": False,
                "max_zero_shift": 0.15,
            },
            "modalities": {
                "text": {"shape": [1, 4], "values": [0.0, 0.0, 0.0, 0.0]},
                "video": {"shape": [1, 4], "values": [0.8, 0.6, 0.4, 0.2]},
            },
        },
    )
    assert warning_response.status_code == 200
    warning_payload = warning_response.json()
    assert warning_payload["warnings"]
    assert any(
        "Population baseline video-cohort-001 drift score" in item
        for item in warning_payload["warnings"]
    )

    blocked_response = client.post(
        "/v1/infer",
        json={
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "classification",
            "num_classes": 2,
            "metadata": {
                "request_id": "block-003",
                "population_baseline_label": "video-cohort-001",
                "block_population_drift": True,
                "max_zero_shift": 0.15,
            },
            "modalities": {
                "text": {"shape": [1, 4], "values": [0.0, 0.0, 0.0, 0.0]},
                "video": {"shape": [1, 4], "values": [0.8, 0.6, 0.4, 0.2]},
            },
        },
    )
    assert blocked_response.status_code == 409
    blocked_payload = blocked_response.json()["detail"]
    assert blocked_payload["baseline_label"] == "video-cohort-001"
    assert blocked_payload["blocked"] is True


def test_pipeline_ingest_persists_a_real_run_record():
    baseline_request = {
        "label": "pipeline-cohort-001",
        "request": {
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "embedding",
            "metadata": {"request_id": "baseline-004"},
            "modalities": {
                "text": {"shape": [2, 4], "values": [0.1, 0.2, 0.3, 0.4, 0.2, 0.3, 0.4, 0.5]},
                "audio": {"shape": [2, 4], "values": [0.5, 0.4, 0.3, 0.2, 0.4, 0.3, 0.2, 0.1]},
            },
        },
    }
    assert client.post("/v1/drift/baselines", json=baseline_request).status_code == 200

    response = client.post(
        "/v1/pipelines/ingest",
        json={
            "stream_id": "concert-intake",
            "batch_label": "window-01",
            "model_id": "adaptive_transformer",
            "runtime_mode": "contract",
            "target": "embedding",
            "baseline_label": "pipeline-cohort-001",
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
                    "source": "audio-monitor",
                    "modality": "audio",
                    "tensor": {"shape": [1, 4], "values": [0.5, 0.4, 0.3, 0.2]},
                },
                {
                    "source": "audio-monitor",
                    "modality": "audio",
                    "tensor": {"shape": [1, 4], "values": [0.4, 0.3, 0.2, 0.1]},
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["event_count"] == 4
    assert payload["paired_batch_size"] == 2
    assert payload["inference"] is not None
    assert payload["provenance"]["payload_digest"]

    run_record = client.get(f"/v1/pipelines/runs/{payload['run_id']}")
    assert run_record.status_code == 200
    assert run_record.json()["stream_id"] == "concert-intake"

    export_record = client.get(f"/v1/pipelines/runs/{payload['run_id']}/export")
    assert export_record.status_code == 200
    exported = export_record.json()
    assert exported["request_snapshot"]["metadata"]["stream_id"] == "concert-intake"
    assert exported["event_lineage"]
    assert exported["replay_frames"]
    assert "caption-feed" in exported["event_ndjson"]
    assert any(item["artifact"] == "request_snapshot" for item in exported["artifact_digests"])
    assert any(item["artifact"] == "replay_frames" for item in exported["artifact_digests"])

    replay_record = client.post(f"/v1/pipelines/runs/{payload['run_id']}/replay")
    assert replay_record.status_code == 200
    replayed = replay_record.json()
    assert replayed["provenance_match"] is True
    assert replayed["summary_shape_match"] is True
    assert replayed["frame_parity_match"] is True
    assert replayed["frame_count"] == len(exported["replay_frames"])
    assert replayed["recorded_head_digest"]
    assert replayed["replayed_head_digest"]
    assert replayed["replay_response"] is not None


def test_ontology_ingest_builds_a_snapshot_with_constraints():
    response = client.post(
        "/v1/ontology/ingest",
        json={
            "tenant_id": "north-star-health",
            "label": "care-governance-v1",
            "zone_cells": {"EU": ["8a2a1072b59ffff"], "US": ["8a2a1072b597fff"]},
            "artifacts": [
                {
                    "title": "Patient API schema",
                    "artifact_type": "api_schema",
                    "control_depth": "surface",
                    "body": "POST /patients/export stores patient records for transfer.",
                    "tags": ["patient", "export", "records"],
                },
                {
                    "title": "Cross-border contract",
                    "artifact_type": "contract",
                    "control_depth": "governance",
                    "body": (
                        "Client data must not move from EU to US. "
                        "PII must stay encrypted in transit and requires review under GDPR."
                    ),
                    "tags": ["gdpr", "pii", "encryption"],
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "north-star-health"
    assert payload["entities"]
    assert payload["constraints"]
    assert any(item["action"] == "block" for item in payload["constraints"])
    assert any(item["action"] == "require_encryption" for item in payload["constraints"])


def test_ontology_liability_surface_flags_cross_border_violation():
    snapshot = client.post(
        "/v1/ontology/ingest",
        json={
            "tenant_id": "north-star-finance",
            "label": "finance-governance-v1",
            "artifacts": [
                {
                    "title": "Treasury route",
                    "artifact_type": "api_schema",
                    "control_depth": "surface",
                    "body": "POST /finance/transfer routes transfer requests.",
                },
                {
                    "title": "Treasury service agreement",
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
    assert snapshot.status_code == 200
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
    assert liability.status_code == 200
    payload = liability.json()
    assert payload["heatmap"]
    assert "/finance/transfer" in payload["blocked_routes"]
    assert any(
        "encrypted transport lane" in finding for finding in payload["heatmap"][0]["findings"]
    )


def test_video_clean_job_persists_a_completed_record():
    submission = client.post(
        "/v1/jobs/video-clean",
        json={
            "clip_id": "job-clip-01",
            "duration_ms": 3000,
            "transcript": [
                {"token": "uh", "start_ms": 0, "end_ms": 100},
                {"token": "hello", "start_ms": 800, "end_ms": 1100},
            ],
        },
    )
    assert submission.status_code == 200
    payload = submission.json()
    record = client.get(f"/v1/jobs/{payload['job_id']}")
    assert record.status_code == 200
    job = record.json()
    assert job["kind"] == "video_clean"
    assert job["status"] == "completed"
    assert "removed_spans" in job["result_payload"]


def test_batch_infer_job_persists_results():
    submission = client.post(
        "/v1/jobs/batch-infer",
        json={
            "label": "batch-01",
            "requests": [
                {
                    "model_id": "adaptive_transformer",
                    "runtime_mode": "contract",
                    "target": "embedding",
                    "modalities": {"text": {"shape": [1, 4], "values": [0.1, 0.2, 0.3, 0.4]}},
                },
                {
                    "model_id": "adaptive_transformer",
                    "runtime_mode": "contract",
                    "target": "classification",
                    "num_classes": 2,
                    "modalities": {"audio": {"shape": [1, 4], "values": [0.4, 0.3, 0.2, 0.1]}},
                },
            ],
        },
    )
    assert submission.status_code == 200
    payload = submission.json()
    record = client.get(f"/v1/jobs/{payload['job_id']}")
    assert record.status_code == 200
    job = record.json()
    assert job["kind"] == "batch_infer"
    assert job["status"] == "completed"
    assert job["result_payload"]["record_count"] == 2
    assert len(job["result_payload"]["results"]) == 2


def test_video_clean_endpoint_surfaces_removed_spans():
    response = client.post(
        "/v1/video/clean",
        json={
            "clip_id": "clip-01",
            "duration_ms": 4000,
            "transcript": [
                {"token": "um", "start_ms": 0, "end_ms": 220},
                {"token": "hello", "start_ms": 900, "end_ms": 1250},
                {"token": "world", "start_ms": 1350, "end_ms": 1600},
            ],
            "frames": [
                {
                    "index": 0,
                    "timestamp_ms": 100,
                    "motion_score": 0.2,
                    "focus_score": 0.8,
                    "brightness": 0.5,
                },
                {
                    "index": 1,
                    "timestamp_ms": 1100,
                    "motion_score": 0.3,
                    "focus_score": 0.7,
                    "brightness": 0.6,
                },
            ],
            "audio_energy": [
                {"timestamp_ms": 150, "energy": 0.4},
                {"timestamp_ms": 1050, "energy": 0.9},
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["removed_spans"]
    assert payload["kept_duration_ms"] < 4000


def test_stream_endpoint_emits_plan_and_result():
    with client.websocket_connect("/v1/stream") as websocket:
        websocket.send_json(
            {
                "model_id": "adaptive_transformer",
                "runtime_mode": "contract",
                "target": "embedding",
                "modalities": {"text": {"shape": [1, 4], "values": [0.2, 0.4, 0.6, 0.8]}},
            }
        )
        first = websocket.receive_json()
        assert first["event"] == "accepted"
        second = websocket.receive_json()
        assert second["event"] == "plan"
        final = None
        while True:
            payload = websocket.receive_json()
            if payload["event"] == "result":
                final = payload
                break
        assert final is not None
        assert final["payload"]["runtime_mode"] == "contract"
