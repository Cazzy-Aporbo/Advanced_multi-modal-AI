from __future__ import annotations

from statistics import mean
from typing import Iterable, List

from .contracts import (
    AudioEnergyPoint,
    FrameSignal,
    SuggestedCut,
    TimeSpan,
    TranscriptToken,
    VideoCleaningRequest,
    VideoCleaningResponse,
    VideoEvidenceWindow,
    VideoPacketRequest,
    VideoPacketResponse,
)


def _excerpt(tokens: Iterable[TranscriptToken], limit: int = 8) -> str:
    words = [token.token for token in list(tokens)[:limit]]
    return " ".join(words).strip()


def _slice_frames(frames: List[FrameSignal], start_ms: int, end_ms: int) -> List[FrameSignal]:
    return [frame for frame in frames if start_ms <= frame.timestamp_ms <= end_ms]


def _slice_audio(
    audio_energy: List[AudioEnergyPoint], start_ms: int, end_ms: int
) -> List[AudioEnergyPoint]:
    return [point for point in audio_energy if start_ms <= point.timestamp_ms <= end_ms]


def _average_frame_metric(frames: List[FrameSignal], attr: str) -> float:
    if not frames:
        return 0.0
    return float(mean(getattr(frame, attr) for frame in frames))


def _average_audio_energy(points: List[AudioEnergyPoint]) -> float:
    if not points:
        return 0.0
    return float(mean(point.energy for point in points))


def _build_windows(
    request: VideoPacketRequest, window_gap_ms: int = 1600
) -> List[VideoEvidenceWindow]:
    if not request.transcript:
        frames = _slice_frames(request.frames, 0, request.duration_ms)
        audio = _slice_audio(request.audio_energy, 0, request.duration_ms)
        return [
            VideoEvidenceWindow(
                span=TimeSpan(start_ms=0, end_ms=request.duration_ms),
                transcript_excerpt="",
                average_motion=_average_frame_metric(frames, "motion_score"),
                average_focus=_average_frame_metric(frames, "focus_score"),
                average_audio_energy=_average_audio_energy(audio),
                note="Signal-only window: no transcript was provided for this clip.",
            )
        ]

    windows: List[VideoEvidenceWindow] = []
    buffer: List[TranscriptToken] = []
    start_ms = request.transcript[0].start_ms
    end_ms = request.transcript[0].end_ms

    for token in request.transcript:
        if buffer and token.start_ms - end_ms > window_gap_ms:
            frames = _slice_frames(request.frames, start_ms, end_ms)
            audio = _slice_audio(request.audio_energy, start_ms, end_ms)
            windows.append(
                VideoEvidenceWindow(
                    span=TimeSpan(start_ms=start_ms, end_ms=end_ms),
                    transcript_excerpt=_excerpt(buffer),
                    average_motion=_average_frame_metric(frames, "motion_score"),
                    average_focus=_average_frame_metric(frames, "focus_score"),
                    average_audio_energy=_average_audio_energy(audio),
                    note="A stable reading window assembled from contiguous transcript timing.",
                )
            )
            buffer = []
            start_ms = token.start_ms
        buffer.append(token)
        end_ms = token.end_ms

    if buffer:
        frames = _slice_frames(request.frames, start_ms, end_ms)
        audio = _slice_audio(request.audio_energy, start_ms, end_ms)
        windows.append(
            VideoEvidenceWindow(
                span=TimeSpan(start_ms=start_ms, end_ms=end_ms),
                transcript_excerpt=_excerpt(buffer),
                average_motion=_average_frame_metric(frames, "motion_score"),
                average_focus=_average_frame_metric(frames, "focus_score"),
                average_audio_energy=_average_audio_energy(audio),
                note="A stable reading window assembled from contiguous transcript timing.",
            )
        )

    return windows


def _detect_filler_cuts(request: VideoCleaningRequest) -> List[SuggestedCut]:
    filler_words = {word.lower() for word in request.filler_words}
    cuts: List[SuggestedCut] = []
    for token in request.transcript:
        if token.token.lower().strip(",.!?") not in filler_words:
            continue
        cuts.append(
            SuggestedCut(
                start_ms=token.start_ms,
                end_ms=min(token.end_ms, token.start_ms + request.max_cut_ms),
                reason="filler_word",
                severity="low",
                transcript_excerpt=token.token,
            )
        )
    return cuts


def _detect_silence_cuts(request: VideoCleaningRequest) -> List[SuggestedCut]:
    if len(request.transcript) < 2:
        return []
    cuts: List[SuggestedCut] = []
    for previous, current in zip(request.transcript, request.transcript[1:], strict=False):
        gap = current.start_ms - previous.end_ms
        if gap < request.silence_threshold_ms:
            continue
        cuts.append(
            SuggestedCut(
                start_ms=previous.end_ms,
                end_ms=min(current.start_ms, previous.end_ms + request.max_cut_ms),
                reason="silence_gap",
                severity="medium" if gap < 1400 else "high",
                transcript_excerpt=f"{previous.token} … {current.token}",
            )
        )
    return cuts


def _merge_cuts(cuts: List[SuggestedCut]) -> List[SuggestedCut]:
    if not cuts:
        return []
    ordered = sorted(cuts, key=lambda cut: (cut.start_ms, cut.end_ms))
    merged: List[SuggestedCut] = [ordered[0]]
    for cut in ordered[1:]:
        current = merged[-1]
        if cut.start_ms <= current.end_ms:
            current.end_ms = max(current.end_ms, cut.end_ms)
            if cut.severity == "high":
                current.severity = "high"
            current.transcript_excerpt = current.transcript_excerpt or cut.transcript_excerpt
            continue
        merged.append(cut)
    return merged


def _build_retained_spans(duration_ms: int, removed_spans: List[SuggestedCut]) -> List[TimeSpan]:
    retained: List[TimeSpan] = []
    cursor = 0
    for span in removed_spans:
        if span.start_ms > cursor:
            retained.append(TimeSpan(start_ms=cursor, end_ms=span.start_ms))
        cursor = max(cursor, span.end_ms)
    if cursor < duration_ms:
        retained.append(TimeSpan(start_ms=cursor, end_ms=duration_ms))
    return retained


def build_video_packet(request: VideoPacketRequest) -> VideoPacketResponse:
    windows = _build_windows(request)
    notes = [
        "This lane reads transcript timing first and uses frame and audio "
        "signals only where they clarify the boundary.",
    ]
    if not request.frames:
        notes.append("No frame signals were provided, so motion and focus remain at zero.")
    if not request.audio_energy:
        notes.append(
            "No audio energy trace was provided, so acoustic stability is "
            "inferred from transcript spacing only."
        )
    return VideoPacketResponse(
        clip_id=request.clip_id,
        objective=request.objective,
        evidence_windows=windows,
        cut_candidates=[],
        notes=notes,
    )


def build_video_cleaning_response(request: VideoCleaningRequest) -> VideoCleaningResponse:
    filler_cuts = _detect_filler_cuts(request)
    silence_cuts = _detect_silence_cuts(request)
    removed = _merge_cuts([*filler_cuts, *silence_cuts])
    retained = _build_retained_spans(request.duration_ms, removed)
    removed_duration_ms = sum(span.end_ms - span.start_ms for span in removed)
    kept_duration_ms = sum(span.end_ms - span.start_ms for span in retained)
    cut_script = [f"cut {span.start_ms}ms->{span.end_ms}ms [{span.reason}]" for span in removed]
    notes = [
        "Cuts are suggested rather than executed. This surface is meant to "
        "prepare an editing or review lane, not silently alter footage.",
    ]
    if not removed:
        notes.append("No filler or silence spans crossed the current thresholds.")
    return VideoCleaningResponse(
        clip_id=request.clip_id,
        removed_spans=removed,
        retained_spans=retained,
        kept_duration_ms=kept_duration_ms,
        removed_duration_ms=removed_duration_ms,
        cut_script=cut_script,
        notes=notes,
    )
