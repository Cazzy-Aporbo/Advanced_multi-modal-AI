CREATE DATABASE IF NOT EXISTS advanced_multimodal_ai;

CREATE TABLE IF NOT EXISTS advanced_multimodal_ai.edge_tracking_events
(
    transaction_id String,
    event_id String,
    route_action String,
    jurisdiction String,
    source_region String,
    target_region String,
    manifest_hash String,
    overall_entropy_score Float64,
    highest_modality_risk Float64,
    encrypted_in_transit UInt8,
    cross_border UInt8,
    connector_kind String,
    ledger_parent_hash String,
    ledger_hash String,
    created_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (created_at, transaction_id);
