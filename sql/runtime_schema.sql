CREATE TABLE IF NOT EXISTS async_jobs (
    job_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT '',
    completed_at TEXT NOT NULL DEFAULT '',
    record_count INTEGER NOT NULL,
    request_payload TEXT NOT NULL,
    result_payload TEXT NOT NULL DEFAULT '{}',
    error_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS dataset_catalog (
    dataset_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    record_payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS connector_runs (
    run_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    connector_kind TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    record_payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS drift_baselines (
    label TEXT PRIMARY KEY,
    baseline_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    runtime_mode TEXT NOT NULL,
    coverage_score REAL NOT NULL,
    fusion_readiness REAL NOT NULL,
    modality_profiles TEXT NOT NULL,
    pairwise_alignment TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,
    stream_id TEXT NOT NULL,
    batch_label TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    record_payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ontology_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    label TEXT NOT NULL,
    created_at TEXT NOT NULL,
    snapshot_payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lifecycle_policies (
    policy_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    record_payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS change_controls (
    change_id TEXT PRIMARY KEY,
    change_kind TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    record_payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS supply_chain_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    created_at TEXT NOT NULL,
    record_payload TEXT NOT NULL
);
