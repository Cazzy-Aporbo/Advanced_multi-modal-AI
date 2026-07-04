from __future__ import annotations

import json

from advanced_multimodal_ai.alignment import build_temporal_alignment
from advanced_multimodal_ai.contracts import (
    EdgePacketRequest,
    InferenceRequest,
    TensorPayload,
    TemporalAlignmentRequest,
    TemporalObservation,
)
from advanced_multimodal_ai.edge_gateway import evaluate_edge_packet
from advanced_multimodal_ai.quality import build_data_profile


def build_casebook() -> dict[str, dict[str, object]]:
    biology_request = InferenceRequest(
        model_id="adaptive_transformer",
        runtime_mode="contract",
        modalities={
            "image": TensorPayload(
                shape=[1, 8],
                values=[0.08, 0.14, 0.09, 0.18, 0.11, 0.17, 0.12, 0.16],
            ),
            "tabular": TensorPayload(
                shape=[1, 8],
                values=[0.07, 0.12, 0.08, 0.15, 0.1, 0.16, 0.11, 0.13],
            ),
            "text": TensorPayload(
                shape=[1, 8],
                values=[0.09, 0.13, 0.1, 0.14, 0.12, 0.15, 0.11, 0.16],
            ),
        },
        metadata={
            "request_id": "micro-biology-window",
            "domain": "biology",
            "question": "Can faint morphology and assay notes stay aligned?",
        },
    )
    media_request = InferenceRequest(
        model_id="adaptive_transformer",
        runtime_mode="contract",
        modalities={
            "audio": TensorPayload(
                shape=[1, 10],
                values=[0.14, 0.19, 0.22, 0.15, 0.11, 0.17, 0.25, 0.18, 0.13, 0.16],
            ),
            "text": TensorPayload(
                shape=[1, 10],
                values=[0.12, 0.14, 0.18, 0.16, 0.13, 0.17, 0.21, 0.19, 0.11, 0.15],
            ),
            "image": TensorPayload(
                shape=[1, 10],
                values=[0.11, 0.18, 0.2, 0.17, 0.1, 0.16, 0.24, 0.21, 0.12, 0.14],
            ),
        },
        metadata={
            "request_id": "micro-media-window",
            "domain": "media",
            "question": "Does a small caption shift change how the same clip reads?",
        },
    )

    alignment = build_temporal_alignment(
        TemporalAlignmentRequest(
            observations=[
                TemporalObservation(
                    modality="audio",
                    start_ms=0,
                    end_ms=420,
                    confidence=0.91,
                    source_id="segment-audio-01",
                ),
                TemporalObservation(
                    modality="text",
                    start_ms=60,
                    end_ms=430,
                    confidence=0.88,
                    source_id="segment-text-01",
                ),
                TemporalObservation(
                    modality="image",
                    start_ms=90,
                    end_ms=410,
                    confidence=0.86,
                    source_id="frame-window-01",
                ),
            ],
            merge_gap_ms=80,
            minimum_modalities=2,
        )
    )
    edge_receipt = evaluate_edge_packet(
        EdgePacketRequest(
            jurisdiction="EU_EEA",
            source_region="NL",
            target_region="NL",
            connector_kind="local_parquet",
            encrypted_in_transit=True,
            modalities=media_request.modalities,
            metadata={"review": "microscopic_signal_pathways"},
        )
    )

    return {
        "biology_micro_window": {
            "profile": build_data_profile(biology_request).model_dump(mode="json"),
            "question": biology_request.metadata["question"],
        },
        "media_micro_window": {
            "profile": build_data_profile(media_request).model_dump(mode="json"),
            "alignment": alignment.model_dump(mode="json"),
            "edge_receipt": edge_receipt.model_dump(mode="json"),
            "question": media_request.metadata["question"],
        },
    }


def main() -> None:
    print(json.dumps(build_casebook(), indent=2))


if __name__ == "__main__":
    main()
