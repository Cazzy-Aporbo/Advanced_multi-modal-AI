from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

import numpy as np

from .contracts import InferenceRequest, PipelineEvent, PipelineIngestRequest, TensorPayload


def build_inference_request_from_pipeline(
    request: PipelineIngestRequest,
) -> tuple[InferenceRequest, Dict[str, int], int]:
    grouped: Dict[str, List[np.ndarray]] = defaultdict(list)
    modality_counts: Dict[str, int] = {}

    for event in request.events:
        row = _flatten_event_tensor(event)
        grouped[event.modality].append(row)

    for modality, rows in grouped.items():
        widths = {int(row.shape[0]) for row in rows}
        if len(widths) != 1:
            raise ValueError(
                f"Pipeline ingest expected a consistent feature width for {modality}, "
                f"received widths {sorted(widths)}"
            )
        modality_counts[modality] = len(rows)

    batch_size = min(modality_counts.values())
    dropped_events = sum(count - batch_size for count in modality_counts.values())

    modalities: Dict[str, TensorPayload] = {}
    for modality, rows in grouped.items():
        stacked = np.stack(rows[:batch_size], axis=0).astype(np.float32)
        modalities[modality] = TensorPayload(
            shape=list(stacked.shape),
            values=stacked.reshape(-1).tolist(),
        )

    inference_request = InferenceRequest(
        model_id=request.model_id,
        runtime_mode=request.runtime_mode,
        target=request.target,
        num_classes=request.num_classes,
        modalities=modalities,
        metadata={
            "stream_id": request.stream_id,
            "batch_label": request.batch_label,
            "event_count": len(request.events),
            "paired_batch_size": batch_size,
            "dropped_events": dropped_events,
        },
    )
    return inference_request, modality_counts, dropped_events


def _flatten_event_tensor(event: PipelineEvent) -> np.ndarray:
    array = np.asarray(event.tensor.values, dtype=np.float32).reshape(event.tensor.shape)
    return array.reshape(-1)
