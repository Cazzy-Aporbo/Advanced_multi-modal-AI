from __future__ import annotations

from statistics import mean
from typing import Dict, List, cast

from .contracts import (
    TemporalAlignmentRequest,
    TemporalAlignmentResponse,
    TemporalAlignmentWindow,
    TimeSpan,
)


def build_temporal_alignment(
    request: TemporalAlignmentRequest,
) -> TemporalAlignmentResponse:
    ordered = sorted(
        request.observations,
        key=lambda item: (item.start_ms, item.end_ms, item.modality),
    )
    windows: List[TemporalAlignmentWindow] = []
    coverage: Dict[str, int] = {}

    current_group = [ordered[0]]
    current_start = ordered[0].start_ms
    current_end = ordered[0].end_ms

    def flush_group() -> None:
        nonlocal current_group, current_start, current_end
        modalities = sorted({item.modality for item in current_group})
        if len(modalities) < request.minimum_modalities and not request.include_singletons:
            return
        source_ids = sorted({item.source_id for item in current_group if item.source_id})
        average_confidence = float(mean(item.confidence for item in current_group))
        for item in current_group:
            coverage[item.modality] = coverage.get(item.modality, 0) + (
                item.end_ms - item.start_ms
            )
        note = (
            "Multiple modalities overlap within one governed window."
            if len(modalities) > 1
            else "A single modality occupies this window without corroboration."
        )
        windows.append(
            TemporalAlignmentWindow(
                span=TimeSpan(start_ms=current_start, end_ms=current_end),
                modalities=modalities,
                observation_count=len(current_group),
                average_confidence=average_confidence,
                source_ids=source_ids,
                note=note,
            )
        )

    for observation in ordered[1:]:
        if observation.start_ms <= current_end + request.merge_gap_ms:
            current_group.append(observation)
            current_end = max(current_end, observation.end_ms)
            continue
        flush_group()
        current_group = [observation]
        current_start = observation.start_ms
        current_end = observation.end_ms

    flush_group()

    seen_modalities = {item.modality for item in ordered}
    covered_modalities = set(coverage.keys())
    uncovered = sorted(seen_modalities - covered_modalities)

    return TemporalAlignmentResponse(
        windows=windows,
        modality_coverage_ms=cast(Dict[str, int], coverage),
        uncovered_modalities=uncovered,
    )
