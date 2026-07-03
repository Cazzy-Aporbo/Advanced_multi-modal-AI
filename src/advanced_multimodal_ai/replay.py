from __future__ import annotations

import hashlib
import json
import math
import struct
from typing import Any, Iterable

from .config import Settings
from .contracts import (
    InferenceResponse,
    PipelineEvent,
    PipelineReplayFrame,
    PipelineReplayResponse,
    PipelineRunExport,
    PipelineRunRecord,
    ReplayArtifactDigest,
)
from .rust_bridge import replay_frame_from_payload


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
            artifact="replay_frames",
            sha256=_canonical_sha256(
                [frame.model_dump(mode="json") for frame in record.replay_frames]
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
        replay_frames=record.replay_frames,
        artifact_digests=artifact_digests,
        event_ndjson=event_ndjson,
        created_at=record.created_at,
    )


def build_replay_frames(
    *,
    events: list[PipelineEvent],
    stream_id: str,
    batch_label: str,
    settings: Settings,
) -> list[PipelineReplayFrame]:
    frames: list[PipelineReplayFrame] = []
    parent_digest = ""
    for sequence_id, event in enumerate(events):
        state_seed = _state_seed(
            stream_id=stream_id,
            batch_label=batch_label,
            sequence_id=sequence_id,
            event=event,
        )
        frame_payload = {
            "sequence_id": sequence_id,
            "modality": event.modality,
            "source": event.source,
            "observed_at": event.observed_at,
            "state_seed": state_seed,
            "parent_digest": parent_digest,
            "shape": event.tensor.shape,
            "values": event.tensor.values,
        }
        response = replay_frame_from_payload(frame_payload, settings)
        frame = (
            PipelineReplayFrame.model_validate(response)
            if response is not None
            else _build_frame_fallback(frame_payload)
        )
        frames.append(frame)
        parent_digest = frame.frame_digest
    return frames


def compare_replay(
    *,
    record: PipelineRunRecord,
    replay_response: InferenceResponse,
    replay_provenance_digest: str,
    replay_frames: list[PipelineReplayFrame],
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

    recorded_head_digest = record.replay_frames[-1].frame_digest if record.replay_frames else ""
    replayed_head_digest = replay_frames[-1].frame_digest if replay_frames else ""
    frame_parity_match = _frames_match(record.replay_frames, replay_frames)
    if not frame_parity_match:
        warnings.append(
            "Replay frame digests diverged from the stored execution memory."
        )

    return PipelineReplayResponse(
        run_id=record.run_id,
        provenance_match=record.provenance.payload_digest == replay_provenance_digest,
        route_match=route_match,
        summary_shape_match=summary_shape_match,
        frame_parity_match=frame_parity_match,
        frame_count=len(replay_frames),
        recorded_head_digest=recorded_head_digest,
        replayed_head_digest=replayed_head_digest,
        max_summary_mean_delta=float(max_summary_mean_delta),
        replay_response=replay_response,
        warnings=warnings,
    )


def _frames_match(
    recorded_frames: list[PipelineReplayFrame],
    replay_frames: list[PipelineReplayFrame],
) -> bool:
    if len(recorded_frames) != len(replay_frames):
        return False
    return all(
        recorded.frame_digest == replayed.frame_digest
        and recorded.tensor_digest == replayed.tensor_digest
        and recorded.sequence_id == replayed.sequence_id
        for recorded, replayed in zip(recorded_frames, replay_frames, strict=False)
    )


def _state_seed(
    *,
    stream_id: str,
    batch_label: str,
    sequence_id: int,
    event: PipelineEvent,
) -> int:
    digest = hashlib.sha256()
    digest.update(stream_id.encode("utf-8"))
    digest.update(b"::")
    digest.update(batch_label.encode("utf-8"))
    digest.update(b"::")
    digest.update(str(sequence_id).encode("utf-8"))
    digest.update(b"::")
    digest.update(event.modality.encode("utf-8"))
    digest.update(b"::")
    digest.update(event.source.encode("utf-8"))
    digest.update(b"::")
    digest.update(event.observed_at.encode("utf-8"))
    return int.from_bytes(digest.digest()[:8], "little", signed=False)


def _build_frame_fallback(payload: dict[str, Any]) -> PipelineReplayFrame:
    shape = [int(dimension) for dimension in payload["shape"]]
    values = [float(value) for value in payload["values"]]
    tensor_bytes = _tensor_bytes(shape, values)
    tensor_digest = hashlib.sha256(tensor_bytes).hexdigest()

    digest = hashlib.sha256()
    digest.update(struct.pack("<Q", int(payload["sequence_id"])))
    digest.update(struct.pack("<Q", int(payload["state_seed"])))
    digest.update(payload.get("parent_digest", "").encode("utf-8"))
    digest.update(payload.get("modality", "").encode("utf-8"))
    digest.update(payload.get("source", "").encode("utf-8"))
    digest.update(payload.get("observed_at", "").encode("utf-8"))
    digest.update(tensor_digest.encode("utf-8"))
    frame_digest = digest.hexdigest()

    mean = sum(values) / len(values) if values else 0.0
    variance = (
        sum((value - mean) ** 2 for value in values) / len(values)
        if values
        else 0.0
    )
    energy = sum(value * value for value in values)
    zero_ratio = (
        sum(1 for value in values if abs(value) < 1e-12) / len(values)
        if values
        else 0.0
    )

    return PipelineReplayFrame(
        sequence_id=int(payload["sequence_id"]),
        modality=payload["modality"],
        source=payload.get("source", ""),
        observed_at=payload.get("observed_at", ""),
        state_seed=int(payload["state_seed"]),
        tensor_shape=shape,
        tensor_digest=tensor_digest,
        frame_digest=frame_digest,
        parent_digest=payload.get("parent_digest", ""),
        byte_count=len(tensor_bytes),
        signal_mean=float(mean),
        signal_std=math.sqrt(variance),
        signal_energy=float(energy),
        zero_ratio=float(zero_ratio),
    )


def _tensor_bytes(shape: list[int], values: Iterable[float]) -> bytes:
    blob = bytearray()
    for dimension in shape:
        blob.extend(struct.pack("<Q", int(dimension)))
    for value in values:
        blob.extend(struct.pack("<d", float(value)))
    return bytes(blob)


def _canonical_sha256(payload: Any) -> str:
    digest = hashlib.sha256()
    digest.update(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()
