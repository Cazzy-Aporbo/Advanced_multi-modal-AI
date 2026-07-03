from __future__ import annotations

import hashlib
import json

from .contracts import InferenceRequest, ProvenanceReceipt


def _stable_digest(payload: object) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_provenance_receipt(request: InferenceRequest) -> ProvenanceReceipt:
    request_payload = request.model_dump(mode="json")
    modality_digests = {
        modality: _stable_digest(payload)
        for modality, payload in sorted(request_payload["modalities"].items())
    }
    metadata_digest = _stable_digest(request_payload.get("metadata", {}))
    payload_digest = _stable_digest(
        {
            "model_id": request_payload["model_id"],
            "runtime_mode": request_payload["runtime_mode"],
            "target": request_payload["target"],
            "num_classes": request_payload.get("num_classes"),
            "modalities": request_payload["modalities"],
            "metadata": request_payload.get("metadata", {}),
        }
    )
    notes = [
        "The receipt is deterministic across identical payloads and key ordering.",
        "Metadata and modality tensors are hashed separately so upstream changes remain legible.",
    ]
    return ProvenanceReceipt(
        request_id=str(request_payload.get("metadata", {}).get("request_id", request.model_id)),
        model_id=request.model_id,
        runtime_mode=request.runtime_mode,
        modality_digests=modality_digests,
        metadata_digest=metadata_digest,
        payload_digest=payload_digest,
        notes=notes,
    )
