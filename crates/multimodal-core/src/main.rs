use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::env;
use std::io::{self, Read};

#[derive(Debug, Deserialize)]
struct TensorPayload {
    shape: Vec<usize>,
    values: Vec<f64>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
struct Summary {
    shape: Vec<usize>,
    mean: f64,
    std: f64,
    min: f64,
    max: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct SignatureResponse {
    signature: Vec<Vec<f64>>,
    summary: Summary,
}

#[derive(Debug, Deserialize, Clone)]
struct TranscriptToken {
    token: String,
    start_ms: i64,
    end_ms: i64,
}

#[derive(Debug, Deserialize)]
struct VideoCutsRequest {
    duration_ms: i64,
    transcript: Vec<TranscriptToken>,
    silence_threshold_ms: i64,
    filler_words: Vec<String>,
    max_cut_ms: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
struct SuggestedCut {
    start_ms: i64,
    end_ms: i64,
    reason: String,
    severity: String,
    transcript_excerpt: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
struct TimeSpan {
    start_ms: i64,
    end_ms: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct VideoCutsResponse {
    removed_spans: Vec<SuggestedCut>,
    retained_spans: Vec<TimeSpan>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct SchemaField {
    name: String,
    dtype: String,
    nullable: bool,
}

#[derive(Debug, Deserialize)]
struct SchemaFingerprintRequest {
    dataset_name: String,
    fields: Vec<SchemaField>,
    partition_keys: Vec<String>,
    primary_keys: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
struct SchemaFingerprintResponse {
    canonical_schema: String,
    fingerprint: String,
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let command = args.get(1).map(|value| value.as_str()).unwrap_or("");
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();

    match command {
        "signature" => {
            let payload: TensorPayload = serde_json::from_str(&input).unwrap();
            let response = signature_from_payload(&payload);
            println!("{}", serde_json::to_string(&response).unwrap());
        }
        "video-cuts" => {
            let payload: VideoCutsRequest = serde_json::from_str(&input).unwrap();
            let response = cuts_from_payload(&payload);
            println!("{}", serde_json::to_string(&response).unwrap());
        }
        "schema-fingerprint" => {
            let payload: SchemaFingerprintRequest = serde_json::from_str(&input).unwrap();
            let response = schema_fingerprint(&payload);
            println!("{}", serde_json::to_string(&response).unwrap());
        }
        _ => {
            eprintln!("expected one of: signature, video-cuts, schema-fingerprint");
            std::process::exit(1);
        }
    }
}

fn signature_from_payload(payload: &TensorPayload) -> SignatureResponse {
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
        let deltas: Vec<f64> = row.windows(2).map(|pair| (pair[1] - pair[0]).abs()).collect();
        let delta_mean = if deltas.is_empty() { 0.0 } else { mean(&deltas) };
        let sparsity = row.iter().filter(|value| value.abs() < 1e-6).count() as f64 / row.len() as f64;
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
            max: payload.values.iter().copied().fold(f64::NEG_INFINITY, f64::max),
        },
    }
}

fn cuts_from_payload(payload: &VideoCutsRequest) -> VideoCutsResponse {
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

fn schema_fingerprint(payload: &SchemaFingerprintRequest) -> SchemaFingerprintResponse {
    let fields = payload
        .fields
        .iter()
        .map(|field| {
            format!(
                "{}:{}:{}",
                field.name.trim().to_ascii_lowercase(),
                field.dtype.trim().to_ascii_lowercase(),
                if field.nullable { "nullable" } else { "required" }
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

fn mean(values: &[f64]) -> f64 {
    if values.is_empty() {
        return 0.0;
    }
    values.iter().sum::<f64>() / values.len() as f64
}

fn std(values: &[f64], mean: f64) -> f64 {
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
}
