from __future__ import annotations

import hashlib
import json
from typing import Any

from .contracts import (
    InferenceResponse,
    PipelineReplayResponse,
    PipelineRunExport,
    PipelineRunRecord,
    ReplayArtifactDigest,
)


def export_pipeline_run(record: PipelineRunRecord) -> PipelineRunExport:
    event_ndjson = "\n".join(
        json.dumps(event.model_dump(mode="json"), sort_keys=True)
        for event in record.event_lineage
    )
    artifact_digests = [
        ReplayArtifactDigest(
            artifact="event_lineage",
            sha256=_canonical_sha256(
                [event.model_dump(mode="json") for event in record.event_lineage]
            ),
        ),
        ReplayArtifactDigest(
            artifact="profile",
            sha256=_canonical_sha256(record.profile.model_dump(mode="json")),
        ),
        ReplayArtifactDigest(
            artifact="provenance",
            sha256=_canonical_sha256(record.provenance.model_dump(mode="json")),
        ),
    ]
    if record.request_snapshot is not None:
        artifact_digests.insert(
            0,
            ReplayArtifactDigest(
                artifact="request_snapshot",
                sha256=_canonical_sha256(record.request_snapshot.model_dump(mode="json")),
            ),
        )
    if record.drift is not None:
        artifact_digests.append(
            ReplayArtifactDigest(
                artifact="drift",
                sha256=_canonical_sha256(record.drift.model_dump(mode="json")),
            )
        )
    if record.inference is not None:
        artifact_digests.append(
            ReplayArtifactDigest(
                artifact="inference",
                sha256=_canonical_sha256(record.inference.model_dump(mode="json")),
            )
        )

    return PipelineRunExport(
        run_id=record.run_id,
        stream_id=record.stream_id,
        batch_label=record.batch_label,
        status=record.status,
        request_snapshot=record.request_snapshot,
        event_lineage=record.event_lineage,
        artifact_digests=artifact_digests,
        event_ndjson=event_ndjson,
        created_at=record.created_at,
    )


def compare_replay(
    record: PipelineRunRecord,
    replay_response: InferenceResponse,
    replay_provenance_digest: str,
) -> PipelineReplayResponse:
    recorded_inference = record.inference
    warnings: list[str] = []
    route_match = True
    summary_shape_match = True
    max_summary_mean_delta = 0.0

    if recorded_inference is None:
        warnings.append(
            "The original pipeline run was held out before inference, so only "
            "the replay result is available."
        )
        route_match = False
        summary_shape_match = False
    else:
        route_match = recorded_inference.route == replay_response.route
        if not route_match:
            warnings.append("Replay route differs from the stored inference route.")

        recorded_keys = set(recorded_inference.summaries)
        replay_keys = set(replay_response.summaries)
        summary_shape_match = recorded_keys == replay_keys and all(
            recorded_inference.summaries[key].shape == replay_response.summaries[key].shape
            for key in recorded_keys & replay_keys
        )
        if not summary_shape_match:
            warnings.append(
                "At least one replay summary shape diverged from the stored run."
            )

        mean_deltas = []
        for key in recorded_keys & replay_keys:
            mean_deltas.append(
                abs(
                    recorded_inference.summaries[key].mean
                    - replay_response.summaries[key].mean
                )
            )
        max_summary_mean_delta = max(mean_deltas, default=0.0)
        if max_summary_mean_delta > 1e-6:
            warnings.append(
                "Replay summary means drifted slightly from the stored result."
            )

    return PipelineReplayResponse(
        run_id=record.run_id,
        provenance_match=record.provenance.payload_digest == replay_provenance_digest,
        route_match=route_match,
        summary_shape_match=summary_shape_match,
        max_summary_mean_delta=float(max_summary_mean_delta),
        replay_response=replay_response,
        warnings=warnings,
    )


def _canonical_sha256(payload: Any) -> str:
    digest = hashlib.sha256()
    digest.update(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()
