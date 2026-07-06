use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Deserialize)]
pub struct TensorPayload {
    pub shape: Vec<usize>,
    pub values: Vec<f64>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct Summary {
    pub shape: Vec<usize>,
    pub mean: f64,
    pub std: f64,
    pub min: f64,
    pub max: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SignatureResponse {
    pub signature: Vec<Vec<f64>>,
    pub summary: Summary,
}

#[derive(Debug, Deserialize, Clone)]
pub struct TranscriptToken {
    pub token: String,
    pub start_ms: i64,
    pub end_ms: i64,
}

#[derive(Debug, Deserialize)]
pub struct VideoCutsRequest {
    pub duration_ms: i64,
    pub transcript: Vec<TranscriptToken>,
    pub silence_threshold_ms: i64,
    pub filler_words: Vec<String>,
    pub max_cut_ms: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct SuggestedCut {
    pub start_ms: i64,
    pub end_ms: i64,
    pub reason: String,
    pub severity: String,
    pub transcript_excerpt: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct TimeSpan {
    pub start_ms: i64,
    pub end_ms: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct VideoCutsResponse {
    pub removed_spans: Vec<SuggestedCut>,
    pub retained_spans: Vec<TimeSpan>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct SchemaField {
    pub name: String,
    pub dtype: String,
    pub nullable: bool,
}

#[derive(Debug, Deserialize)]
pub struct SchemaFingerprintRequest {
    pub dataset_name: String,
    pub fields: Vec<SchemaField>,
    pub partition_keys: Vec<String>,
    pub primary_keys: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct SchemaFingerprintResponse {
    pub canonical_schema: String,
    pub fingerprint: String,
}

#[derive(Debug, Deserialize)]
pub struct TensorGuardRequest {
    pub shape: Vec<usize>,
    pub values: Vec<f64>,
    pub max_risk: Option<f64>,
    pub max_entropy: Option<f64>,
    pub max_spatial_frequency: Option<f64>,
    pub watch_margin: Option<f64>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct TensorGuardResponse {
    pub entropy_score: f64,
    pub spatial_frequency: f64,
    pub saturation_ratio: f64,
    pub zero_ratio: f64,
    pub risk_score: f64,
    pub status: String,
    pub notes: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct ReplayFrameRequest {
    pub sequence_id: u64,
    pub modality: String,
    pub source: String,
    pub observed_at: String,
    pub state_seed: u64,
    pub parent_digest: String,
    pub shape: Vec<usize>,
    pub values: Vec<f64>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct ReplayFrameResponse {
    pub sequence_id: u64,
    pub modality: String,
    pub source: String,
    pub observed_at: String,
    pub state_seed: u64,
    pub tensor_shape: Vec<usize>,
    pub tensor_digest: String,
    pub frame_digest: String,
    pub parent_digest: String,
    pub byte_count: usize,
    pub signal_mean: f64,
    pub signal_std: f64,
    pub signal_energy: f64,
    pub zero_ratio: f64,
}

#[derive(Debug, Deserialize, Clone)]
pub struct NamedTensorPayload {
    pub modality: String,
    pub shape: Vec<usize>,
    pub values: Vec<f64>,
}

#[derive(Debug, Deserialize)]
pub struct QualityReceiptRequest {
    pub request_id: String,
    pub tensors: Vec<NamedTensorPayload>,
    pub max_risk: Option<f64>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct ModalityQualityReceipt {
    pub modality: String,
    pub value_count: usize,
    pub finite_ratio: f64,
    pub mean: f64,
    pub std: f64,
    pub entropy_score: f64,
    pub spatial_frequency: f64,
    pub risk_score: f64,
    pub status: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct QualityReceiptResponse {
    pub request_id: String,
    pub modality_count: usize,
    pub total_values: usize,
    pub readiness_score: f64,
    pub status: String,
    pub receipt_digest: String,
    pub modalities: Vec<ModalityQualityReceipt>,
}

pub fn signature_from_payload(payload: &TensorPayload) -> SignatureResponse {
    let batch = payload.shape.first().copied().unwrap_or(1).max(1);
    let flat_width = payload.values.len() / batch;
    let rows: Vec<&[f64]> = payload.values.chunks(flat_width.max(1)).collect();

    let mut signatures = Vec::with_capacity(rows.len());
    for row in rows {
        let row_mean = mean(row);
        let row_std = std(row, row_mean);
        let row_min = row.iter().copied().fold(f64::INFINITY, f64::min);
        let row_max = row.iter().copied().fold(f64::NEG_INFINITY, f64::max);
        let abs_mean = mean(&row.iter().map(|value| value.abs()).collect::<Vec<_>>());
        let rms = (row.iter().map(|value| value.powi(2)).sum::<f64>() / row.len() as f64).sqrt();
        let deltas: Vec<f64> = row
            .windows(2)
            .map(|pair| (pair[1] - pair[0]).abs())
            .collect();
        let delta_mean = if deltas.is_empty() {
            0.0
        } else {
            mean(&deltas)
        };
        let sparsity =
            row.iter().filter(|value| value.abs() < 1e-6).count() as f64 / row.len() as f64;
        signatures.push(vec![
            row_mean, row_std, row_min, row_max, abs_mean, rms, delta_mean, sparsity,
        ]);
    }

    let global_mean = mean(&payload.values);
    SignatureResponse {
        signature: signatures,
        summary: Summary {
            shape: payload.shape.clone(),
            mean: global_mean,
            std: std(&payload.values, global_mean),
            min: payload.values.iter().copied().fold(f64::INFINITY, f64::min),
            max: payload
                .values
                .iter()
                .copied()
                .fold(f64::NEG_INFINITY, f64::max),
        },
    }
}

pub fn cuts_from_payload(payload: &VideoCutsRequest) -> VideoCutsResponse {
    let filler_words: Vec<String> = payload
        .filler_words
        .iter()
        .map(|word| word.to_ascii_lowercase())
        .collect();
    let mut removed = Vec::new();

    for token in &payload.transcript {
        let normalized = token
            .token
            .trim_matches(|char: char| ",.!?".contains(char))
            .to_ascii_lowercase();
        if filler_words.contains(&normalized) {
            removed.push(SuggestedCut {
                start_ms: token.start_ms,
                end_ms: (token.end_ms).min(token.start_ms + payload.max_cut_ms),
                reason: "filler_word".to_string(),
                severity: "low".to_string(),
                transcript_excerpt: token.token.clone(),
            });
        }
    }

    for pair in payload.transcript.windows(2) {
        let previous = &pair[0];
        let current = &pair[1];
        let gap = current.start_ms - previous.end_ms;
        if gap >= payload.silence_threshold_ms {
            removed.push(SuggestedCut {
                start_ms: previous.end_ms,
                end_ms: current.start_ms.min(previous.end_ms + payload.max_cut_ms),
                reason: "silence_gap".to_string(),
                severity: if gap < 1400 { "medium" } else { "high" }.to_string(),
                transcript_excerpt: format!("{} … {}", previous.token, current.token),
            });
        }
    }

    removed.sort_by_key(|span| (span.start_ms, span.end_ms));
    let mut merged: Vec<SuggestedCut> = Vec::new();
    for span in removed {
        if let Some(last) = merged.last_mut() {
            if span.start_ms <= last.end_ms {
                last.end_ms = last.end_ms.max(span.end_ms);
                if span.severity == "high" {
                    last.severity = "high".to_string();
                }
                continue;
            }
        }
        merged.push(span);
    }

    let mut retained = Vec::new();
    let mut cursor = 0_i64;
    for span in &merged {
        if span.start_ms > cursor {
            retained.push(TimeSpan {
                start_ms: cursor,
                end_ms: span.start_ms,
            });
        }
        cursor = cursor.max(span.end_ms);
    }
    if cursor < payload.duration_ms {
        retained.push(TimeSpan {
            start_ms: cursor,
            end_ms: payload.duration_ms,
        });
    }

    VideoCutsResponse {
        removed_spans: merged,
        retained_spans: retained,
    }
}

pub fn schema_fingerprint(payload: &SchemaFingerprintRequest) -> SchemaFingerprintResponse {
    let fields = payload
        .fields
        .iter()
        .map(|field| {
            format!(
                "{}:{}:{}",
                field.name.trim().to_ascii_lowercase(),
                field.dtype.trim().to_ascii_lowercase(),
                if field.nullable {
                    "nullable"
                } else {
                    "required"
                }
            )
        })
        .collect::<Vec<_>>()
        .join("|");
    let partition_keys = payload
        .partition_keys
        .iter()
        .map(|value| value.trim().to_ascii_lowercase())
        .collect::<Vec<_>>()
        .join(",");
    let primary_keys = payload
        .primary_keys
        .iter()
        .map(|value| value.trim().to_ascii_lowercase())
        .collect::<Vec<_>>()
        .join(",");
    let canonical_schema = format!(
        "dataset={};fields={};partition={};primary={}",
        payload.dataset_name.trim().to_ascii_lowercase(),
        fields,
        partition_keys,
        primary_keys
    );
    let mut hasher = Sha256::new();
    hasher.update(canonical_schema.as_bytes());
    let fingerprint = format!("{:x}", hasher.finalize());
    SchemaFingerprintResponse {
        canonical_schema,
        fingerprint,
    }
}

pub fn tensor_guard(payload: &TensorGuardRequest) -> TensorGuardResponse {
    let batch = payload.shape.first().copied().unwrap_or(1).max(1);
    let flat_width = (payload.values.len() / batch).max(1);
    let rows: Vec<&[f64]> = payload.values.chunks(flat_width).collect();
    let entropy_score = normalized_entropy(&payload.values, 12);
    let zero_ratio = payload
        .values
        .iter()
        .filter(|value| value.abs() < 1e-6)
        .count() as f64
        / payload.values.len().max(1) as f64;
    let spatial_frequency = normalized_spatial_frequency(&rows);
    let saturation_ratio = saturation_ratio(&payload.values);
    let risk_score = risk_score(
        entropy_score,
        spatial_frequency,
        saturation_ratio,
        zero_ratio,
    );

    let max_risk = payload.max_risk.unwrap_or(0.74);
    let max_entropy = payload.max_entropy.unwrap_or(0.92);
    let max_spatial_frequency = payload.max_spatial_frequency.unwrap_or(0.58);
    let watch_margin = payload.watch_margin.unwrap_or(0.10);
    let mut status = "ok".to_string();
    let mut notes = Vec::new();

    if entropy_score >= max_entropy {
        notes.push(
            "Entropy is high enough that the tensor carries a dense signal field.".to_string(),
        );
        status = "watch".to_string();
    }
    if spatial_frequency >= max_spatial_frequency {
        notes.push(
            "Spatial frequency is elevated, which often marks image- or waveform-heavy content."
                .to_string(),
        );
        status = "watch".to_string();
    }
    if risk_score >= max_risk {
        notes.push(
            "The combined geometric risk crossed the current intercept threshold.".to_string(),
        );
        status = "fail".to_string();
    } else if risk_score >= (max_risk - watch_margin).max(0.0) && status == "ok" {
        notes.push(
            "The combined geometric risk is close to the configured intercept threshold."
                .to_string(),
        );
        status = "watch".to_string();
    }

    TensorGuardResponse {
        entropy_score,
        spatial_frequency,
        saturation_ratio,
        zero_ratio,
        risk_score,
        status,
        notes,
    }
}

pub fn replay_frame(payload: &ReplayFrameRequest) -> ReplayFrameResponse {
    let tensor_bytes = tensor_bytes(&payload.shape, &payload.values);

    let mut tensor_hasher = Sha256::new();
    tensor_hasher.update(&tensor_bytes);
    let tensor_digest = format!("{:x}", tensor_hasher.finalize());

    let mut frame_hasher = Sha256::new();
    frame_hasher.update(payload.sequence_id.to_le_bytes());
    frame_hasher.update(payload.state_seed.to_le_bytes());
    frame_hasher.update(payload.parent_digest.as_bytes());
    frame_hasher.update(payload.modality.as_bytes());
    frame_hasher.update(payload.source.as_bytes());
    frame_hasher.update(payload.observed_at.as_bytes());
    frame_hasher.update(tensor_digest.as_bytes());
    let frame_digest = format!("{:x}", frame_hasher.finalize());

    let timestamp_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos() as u64;
    let signal_mean = mean(&payload.values);
    let signal_std = std(&payload.values, signal_mean);
    let signal_energy = payload
        .values
        .iter()
        .map(|value| value * value)
        .sum::<f64>();
    let zero_ratio = payload
        .values
        .iter()
        .filter(|value| value.abs() < 1e-12)
        .count() as f64
        / payload.values.len().max(1) as f64;

    ReplayFrameResponse {
        sequence_id: payload.sequence_id,
        modality: payload.modality.clone(),
        source: payload.source.clone(),
        observed_at: if payload.observed_at.is_empty() {
            timestamp_ns.to_string()
        } else {
            payload.observed_at.clone()
        },
        state_seed: payload.state_seed,
        tensor_shape: payload.shape.clone(),
        tensor_digest,
        frame_digest,
        parent_digest: payload.parent_digest.clone(),
        byte_count: tensor_bytes.len(),
        signal_mean,
        signal_std,
        signal_energy,
        zero_ratio,
    }
}

pub fn quality_receipt(payload: &QualityReceiptRequest) -> QualityReceiptResponse {
    let max_risk = payload.max_risk.unwrap_or(0.74).clamp(0.0, 1.0);
    let mut modalities = payload
        .tensors
        .iter()
        .map(|tensor| {
            let finite_count = tensor
                .values
                .iter()
                .filter(|value| value.is_finite())
                .count();
            let finite_ratio = finite_count as f64 / tensor.values.len().max(1) as f64;
            let safe_values = tensor
                .values
                .iter()
                .map(|value| if value.is_finite() { *value } else { 0.0 })
                .collect::<Vec<_>>();
            let batch = tensor.shape.first().copied().unwrap_or(1).max(1);
            let flat_width = (safe_values.len() / batch).max(1);
            let rows: Vec<&[f64]> = safe_values.chunks(flat_width).collect();
            let tensor_mean = mean(&safe_values);
            let tensor_std = std(&safe_values, tensor_mean);
            let entropy_score = normalized_entropy(&safe_values, 12);
            let spatial_frequency = normalized_spatial_frequency(&rows);
            let zero_ratio = safe_values
                .iter()
                .filter(|value| value.abs() < 1e-6)
                .count() as f64
                / safe_values.len().max(1) as f64;
            let tensor_risk = risk_score(
                entropy_score,
                spatial_frequency,
                saturation_ratio(&safe_values),
                zero_ratio,
            );
            let status = if finite_ratio < 1.0 || tensor_risk >= max_risk {
                "fail"
            } else if tensor_risk >= (max_risk - 0.12).max(0.0) || entropy_score < 0.08 {
                "watch"
            } else {
                "ok"
            };
            ModalityQualityReceipt {
                modality: tensor.modality.trim().to_ascii_lowercase(),
                value_count: tensor.values.len(),
                finite_ratio,
                mean: tensor_mean,
                std: tensor_std,
                entropy_score,
                spatial_frequency,
                risk_score: tensor_risk,
                status: status.to_string(),
            }
        })
        .collect::<Vec<_>>();
    modalities.sort_by(|left, right| left.modality.cmp(&right.modality));

    let total_values = modalities
        .iter()
        .map(|receipt| receipt.value_count)
        .sum::<usize>();
    let readiness_score = if modalities.is_empty() {
        0.0
    } else {
        let mean_risk = modalities
            .iter()
            .map(|receipt| receipt.risk_score)
            .sum::<f64>()
            / modalities.len() as f64;
        let mean_finite = modalities
            .iter()
            .map(|receipt| receipt.finite_ratio)
            .sum::<f64>()
            / modalities.len() as f64;
        ((1.0 - mean_risk) * 0.62 + mean_finite * 0.38).clamp(0.0, 1.0)
    };
    let status = if modalities.is_empty() {
        "fail"
    } else if modalities.iter().any(|receipt| receipt.status == "fail") {
        "fail"
    } else if modalities.iter().any(|receipt| receipt.status == "watch") {
        "watch"
    } else {
        "ok"
    };

    let mut hasher = Sha256::new();
    hasher.update(payload.request_id.as_bytes());
    hasher.update(max_risk.to_le_bytes());
    for tensor in &payload.tensors {
        hasher.update(tensor.modality.trim().to_ascii_lowercase().as_bytes());
        hasher.update(tensor_bytes(&tensor.shape, &tensor.values));
    }
    for receipt in &modalities {
        hasher.update(receipt.modality.as_bytes());
        hasher.update(receipt.value_count.to_le_bytes());
        hasher.update(receipt.finite_ratio.to_le_bytes());
        hasher.update(receipt.risk_score.to_le_bytes());
    }

    QualityReceiptResponse {
        request_id: payload.request_id.clone(),
        modality_count: modalities.len(),
        total_values,
        readiness_score,
        status: status.to_string(),
        receipt_digest: format!("{:x}", hasher.finalize()),
        modalities,
    }
}

pub fn mean(values: &[f64]) -> f64 {
    if values.is_empty() {
        return 0.0;
    }
    values.iter().sum::<f64>() / values.len() as f64
}

pub fn std(values: &[f64], mean: f64) -> f64 {
    if values.is_empty() {
        return 0.0;
    }
    let variance = values
        .iter()
        .map(|value| {
            let diff = value - mean;
            diff * diff
        })
        .sum::<f64>()
        / values.len() as f64;
    variance.sqrt()
}

pub fn normalized_entropy(values: &[f64], bins: usize) -> f64 {
    if values.len() <= 1 {
        return 0.0;
    }
    let lower = values.iter().copied().fold(f64::INFINITY, f64::min);
    let upper = values.iter().copied().fold(f64::NEG_INFINITY, f64::max);
    if (upper - lower).abs() <= 1e-12 {
        return 0.0;
    }
    let bin_count = bins.max(2).min(values.len());
    let mut counts = vec![0_usize; bin_count];
    let scale = (bin_count - 1) as f64 / (upper - lower);
    for value in values {
        let normalized = ((value - lower) * scale).floor();
        let index = normalized.clamp(0.0, (bin_count - 1) as f64) as usize;
        counts[index] += 1;
    }
    let total = values.len() as f64;
    let entropy = counts
        .iter()
        .filter(|count| **count > 0)
        .map(|count| {
            let probability = *count as f64 / total;
            -(probability * probability.log2())
        })
        .sum::<f64>();
    let max_entropy = (bin_count as f64).log2();
    if max_entropy <= 0.0 {
        return 0.0;
    }
    (entropy / max_entropy).clamp(0.0, 1.0)
}

pub fn normalized_spatial_frequency(rows: &[&[f64]]) -> f64 {
    let mut diff_energy = 0.0;
    let mut diff_count = 0_usize;
    let mut lower = f64::INFINITY;
    let mut upper = f64::NEG_INFINITY;
    for row in rows {
        for value in *row {
            lower = lower.min(*value);
            upper = upper.max(*value);
        }
        for pair in row.windows(2) {
            let diff = pair[1] - pair[0];
            diff_energy += diff * diff;
            diff_count += 1;
        }
    }
    if diff_count == 0 {
        return 0.0;
    }
    let dynamic_range = upper - lower;
    if dynamic_range.abs() <= 1e-12 {
        return 0.0;
    }
    let rms = (diff_energy / diff_count as f64).sqrt();
    (rms / dynamic_range).clamp(0.0, 1.0)
}

pub fn saturation_ratio(values: &[f64]) -> f64 {
    let max_abs = values
        .iter()
        .map(|value| value.abs())
        .fold(0.0_f64, f64::max);
    if max_abs <= 1e-12 {
        return 0.0;
    }
    let threshold = max_abs * 0.92;
    values
        .iter()
        .filter(|value| value.abs() >= threshold)
        .count() as f64
        / values.len().max(1) as f64
}

pub fn risk_score(
    entropy_score: f64,
    spatial_frequency: f64,
    saturation_ratio: f64,
    zero_ratio: f64,
) -> f64 {
    let density_score = 1.0 - zero_ratio;
    ((entropy_score * 0.34)
        + (spatial_frequency * 0.34)
        + (saturation_ratio * 0.18)
        + (density_score * 0.14))
        .clamp(0.0, 1.0)
}

fn tensor_bytes(shape: &[usize], values: &[f64]) -> Vec<u8> {
    let mut bytes = Vec::with_capacity((shape.len() * 8) + (values.len() * 8));
    for dimension in shape {
        bytes.extend_from_slice(&(*dimension as u64).to_le_bytes());
    }
    for value in values {
        bytes.extend_from_slice(&value.to_le_bytes());
    }
    bytes
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn signature_response_has_expected_shape() {
        let payload = TensorPayload {
            shape: vec![2, 4],
            values: vec![0.0, 1.0, 2.0, 3.0, 1.0, 1.0, 1.0, 1.0],
        };
        let response = signature_from_payload(&payload);
        assert_eq!(response.signature.len(), 2);
        assert_eq!(response.signature[0].len(), 8);
        assert_eq!(response.summary.shape, vec![2, 4]);
    }

    #[test]
    fn video_cuts_find_fillers_and_silence() {
        let payload = VideoCutsRequest {
            duration_ms: 5000,
            transcript: vec![
                TranscriptToken {
                    token: "um".to_string(),
                    start_ms: 0,
                    end_ms: 180,
                },
                TranscriptToken {
                    token: "hello".to_string(),
                    start_ms: 900,
                    end_ms: 1200,
                },
                TranscriptToken {
                    token: "there".to_string(),
                    start_ms: 2500,
                    end_ms: 2800,
                },
            ],
            silence_threshold_ms: 600,
            filler_words: vec!["um".to_string()],
            max_cut_ms: 1800,
        };

        let response = cuts_from_payload(&payload);
        assert!(response
            .removed_spans
            .iter()
            .any(|span| span.reason == "filler_word"));
        assert!(response
            .removed_spans
            .iter()
            .any(|span| span.reason == "silence_gap"));
        assert!(!response.retained_spans.is_empty());
    }

    #[test]
    fn schema_fingerprint_is_deterministic() {
        let payload = SchemaFingerprintRequest {
            dataset_name: "event_log".to_string(),
            fields: vec![
                SchemaField {
                    name: "tenant_id".to_string(),
                    dtype: "string".to_string(),
                    nullable: false,
                },
                SchemaField {
                    name: "created_at".to_string(),
                    dtype: "timestamp".to_string(),
                    nullable: false,
                },
            ],
            partition_keys: vec!["created_at".to_string()],
            primary_keys: vec!["tenant_id".to_string()],
        };

        let first = schema_fingerprint(&payload);
        let second = schema_fingerprint(&payload);
        assert_eq!(first, second);
        assert!(first.fingerprint.len() >= 32);
    }

    #[test]
    fn tensor_guard_flags_dense_high_frequency_rows() {
        let payload = TensorGuardRequest {
            shape: vec![1, 16],
            values: vec![
                -1.0, 1.0, -0.95, 0.95, -1.0, 1.0, -0.92, 0.92, -1.0, 1.0, -0.95, 0.95, -1.0, 1.0,
                -0.9, 0.9,
            ],
            max_risk: Some(0.55),
            max_entropy: Some(0.75),
            max_spatial_frequency: Some(0.45),
            watch_margin: Some(0.05),
        };

        let response = tensor_guard(&payload);
        assert_eq!(response.status, "fail");
        assert!(response.risk_score >= 0.55);
        assert!(response.spatial_frequency >= 0.45);
    }

    #[test]
    fn replay_frame_chains_the_parent_digest() {
        let first = replay_frame(&ReplayFrameRequest {
            sequence_id: 0,
            modality: "audio".to_string(),
            source: "stream-a".to_string(),
            observed_at: "2026-07-03T00:00:00Z".to_string(),
            state_seed: 42,
            parent_digest: "".to_string(),
            shape: vec![1, 4],
            values: vec![0.1, 0.2, 0.3, 0.4],
        });
        let second = replay_frame(&ReplayFrameRequest {
            sequence_id: 1,
            modality: "audio".to_string(),
            source: "stream-a".to_string(),
            observed_at: "2026-07-03T00:00:01Z".to_string(),
            state_seed: 84,
            parent_digest: first.frame_digest.clone(),
            shape: vec![1, 4],
            values: vec![0.1, 0.2, 0.3, 0.4],
        });
        assert_ne!(first.frame_digest, second.frame_digest);
        assert_eq!(second.parent_digest, first.frame_digest);
        assert_eq!(first.byte_count, 48);
    }

    #[test]
    fn quality_receipt_is_deterministic_across_modalities() {
        let payload = QualityReceiptRequest {
            request_id: "case-001".to_string(),
            max_risk: Some(0.82),
            tensors: vec![
                NamedTensorPayload {
                    modality: "audio".to_string(),
                    shape: vec![1, 6],
                    values: vec![0.0, 0.1, 0.2, 0.1, 0.0, -0.1],
                },
                NamedTensorPayload {
                    modality: "image".to_string(),
                    shape: vec![1, 4],
                    values: vec![0.2, 0.3, 0.4, 0.5],
                },
            ],
        };

        let first = quality_receipt(&payload);
        let second = quality_receipt(&payload);

        assert_eq!(first.receipt_digest, second.receipt_digest);
        assert_eq!(first.modality_count, 2);
        assert_eq!(first.total_values, 10);
        assert_eq!(first.status, "ok");
        assert!(first.readiness_score > 0.0);
    }

    #[test]
    fn quality_receipt_fails_non_finite_payloads() {
        let payload = QualityReceiptRequest {
            request_id: "case-non-finite".to_string(),
            max_risk: Some(0.9),
            tensors: vec![NamedTensorPayload {
                modality: "sensor".to_string(),
                shape: vec![1, 4],
                values: vec![0.1, f64::NAN, 0.2, f64::INFINITY],
            }],
        };

        let response = quality_receipt(&payload);

        assert_eq!(response.status, "fail");
        assert_eq!(response.modalities[0].finite_ratio, 0.5);
        assert!(response.receipt_digest.len() >= 32);
    }

    #[test]
    fn quality_receipt_fails_empty_payloads() {
        let payload = QualityReceiptRequest {
            request_id: "case-empty".to_string(),
            max_risk: Some(0.9),
            tensors: Vec::new(),
        };

        let response = quality_receipt(&payload);

        assert_eq!(response.status, "fail");
        assert_eq!(response.modality_count, 0);
        assert_eq!(response.total_values, 0);
        assert_eq!(response.readiness_score, 0.0);
        assert!(response.receipt_digest.len() >= 32);
    }
}
