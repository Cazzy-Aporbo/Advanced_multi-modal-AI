use multimodal_core::{
    cuts_from_payload, quality_receipt, replay_frame, schema_fingerprint, signature_from_payload,
    tensor_guard, QualityReceiptRequest, ReplayFrameRequest, SchemaFingerprintRequest,
    TensorGuardRequest, TensorPayload, VideoCutsRequest,
};
use std::env;
use std::io::{self, Read};

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
        "tensor-guard" => {
            let payload: TensorGuardRequest = serde_json::from_str(&input).unwrap();
            let response = tensor_guard(&payload);
            println!("{}", serde_json::to_string(&response).unwrap());
        }
        "replay-frame" => {
            let payload: ReplayFrameRequest = serde_json::from_str(&input).unwrap();
            let response = replay_frame(&payload);
            println!("{}", serde_json::to_string(&response).unwrap());
        }
        "quality-receipt" => {
            let payload: QualityReceiptRequest = serde_json::from_str(&input).unwrap();
            let response = quality_receipt(&payload);
            println!("{}", serde_json::to_string(&response).unwrap());
        }
        _ => {
            eprintln!(
                "expected one of: signature, video-cuts, schema-fingerprint, tensor-guard, replay-frame, quality-receipt"
            );
            std::process::exit(1);
        }
    }
}
