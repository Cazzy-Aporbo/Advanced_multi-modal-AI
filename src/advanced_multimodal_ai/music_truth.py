from __future__ import annotations

from collections import Counter
from statistics import mean, median

from .alignment import build_temporal_alignment
from .contracts import (
    MusicChangeEvidence,
    MusicChangeProofResponse,
    MusicDriftIndicator,
    MusicDriftReport,
    MusicFeatureWarehouseRun,
    MusicSegmentInput,
    MusicSegmentRecord,
    MusicTrackManifestRecord,
    MusicWarehouseSnapshot,
    TemporalAlignmentRequest,
    TemporalAlignmentResponse,
    TemporalObservation,
)


def build_segment_index(
    *,
    run_id: str,
    manifest: MusicTrackManifestRecord,
    inputs: list[MusicSegmentInput],
    features: list,
) -> list[MusicSegmentRecord]:
    feature_by_segment = {item.segment_id: item for item in features}
    records: list[MusicSegmentRecord] = []
    for segment in inputs:
        feature = feature_by_segment.get(segment.segment_id)
        flags = _quality_flags(segment=segment, feature=feature)
        records.append(
            MusicSegmentRecord(
                run_id=run_id,
                manifest_id=manifest.manifest_id,
                track_name=manifest.track_name,
                segment_id=segment.segment_id,
                start_ms=segment.start_ms,
                end_ms=segment.end_ms,
                duration_ms=max(segment.end_ms - segment.start_ms, 1),
                label=segment.label,
                speaker=segment.speaker,
                transcript_excerpt=segment.transcript_excerpt,
                transcript_ref=str(segment.attributes.get("transcript_ref", "")),
                section_kind=str(
                    segment.attributes.get("speaker_or_section", segment.label)
                ),
                frame_ref=str(segment.attributes.get("frame_ref", "")),
                video_window_start_ms=_optional_int(
                    segment.attributes.get("video_window_start_ms")
                ),
                video_window_end_ms=_optional_int(
                    segment.attributes.get("video_window_end_ms")
                ),
                quality_flags=flags,
                attributes=segment.attributes,
            )
        )
    return records


def build_alignment_preview(run: MusicFeatureWarehouseRun) -> TemporalAlignmentResponse:
    observations: list[TemporalObservation] = []
    for segment in run.segment_index:
        observations.append(
            TemporalObservation(
                modality="audio",
                source_id=segment.segment_id,
                start_ms=segment.start_ms,
                end_ms=segment.end_ms,
                confidence=0.92 if not segment.quality_flags else 0.76,
            )
        )
        if segment.transcript_excerpt.strip():
            observations.append(
                TemporalObservation(
                    modality="text",
                    source_id=segment.transcript_ref or segment.segment_id,
                    start_ms=segment.start_ms,
                    end_ms=segment.end_ms,
                    confidence=0.88,
                )
            )
        if (
            segment.video_window_start_ms is not None
            and segment.video_window_end_ms is not None
        ):
            observations.append(
                TemporalObservation(
                    modality="video",
                    source_id=segment.frame_ref or segment.segment_id,
                    start_ms=segment.video_window_start_ms,
                    end_ms=segment.video_window_end_ms,
                    confidence=0.73,
                )
            )
    if not observations:
        return TemporalAlignmentResponse(
            windows=[],
            modality_coverage_ms={},
            uncovered_modalities=[],
        )
    return build_temporal_alignment(
        TemporalAlignmentRequest(
            observations=observations,
            merge_gap_ms=220,
            minimum_modalities=2,
            include_singletons=True,
        )
    )


def build_music_drift_report(
    manifests: list[MusicTrackManifestRecord],
    runs: list[MusicFeatureWarehouseRun],
) -> MusicDriftReport:
    indicators: list[MusicDriftIndicator] = []
    latest_runs = runs[:12]
    segments = [segment for run in latest_runs for segment in run.segments]
    manifest_count = len(manifests)
    feature_run_count = len(runs)

    if segments:
        rms_values = [segment.rms_energy for segment in segments]
        silence_values = [segment.silence_ratio for segment in segments]
        repetition_values = [segment.repetition_ratio for segment in segments]
        dynamic_ranges = [segment.dynamic_range for segment in segments]
        language_counts = Counter(language for item in manifests for language in item.languages)
        region_counts = Counter(region for item in manifests for region in item.regions)
        genre_counts = Counter(genre for item in manifests for genre in item.genres)
        pitch_counts = Counter(segment.dominant_pitch_class for segment in segments)

        indicators.extend(
            [
                _indicator(
                    "loudness-drift",
                    "Loudness drift",
                    score=min(abs(mean(rms_values) - median(rms_values)) * 4.0, 1.0),
                    evidence=(
                        f"Recent RMS energy centers around "
                        f"{mean(rms_values):.3f} with a median of "
                        f"{median(rms_values):.3f}."
                    ),
                    why_it_matters=(
                        "A catalog can look fuller than it is when "
                        "amplitude keeps rising while variation stays flat."
                    ),
                    suggested_action=(
                        "Compare mastering posture across splits before "
                        "treating engagement changes as audience preference."
                    ),
                ),
                _indicator(
                    "language-share-drift",
                    "Language-share drift",
                    score=_top_share(language_counts),
                    evidence=_share_evidence(
                        language_counts,
                        empty_text="No language metadata has been declared yet.",
                    ),
                    why_it_matters=(
                        "A multilingual lane narrows quietly when one language "
                        "becomes the default source of comparison."
                    ),
                    suggested_action=(
                        "Add balanced language coverage to the next manifest "
                        "pass and keep language visible in benchmarking."
                    ),
                ),
                _indicator(
                    "genre-imbalance",
                    "Genre imbalance",
                    score=_top_share(genre_counts),
                    evidence=_share_evidence(
                        genre_counts,
                        empty_text="No genre metadata has been declared yet.",
                    ),
                    why_it_matters=(
                        "Genre imbalance turns discovery metrics into a "
                        "reflection of catalog posture rather than listener breadth."
                    ),
                    suggested_action=(
                        "Widen manifest intake with smaller or regionally "
                        "distinct genres before the warehouse calcifies."
                    ),
                ),
                _indicator(
                    "instrumentation-collapse",
                    "Instrumentation collapse",
                    score=_top_share(pitch_counts),
                    evidence=_share_evidence(
                        pitch_counts,
                        empty_text="Pitch-class diversity has not been measured yet.",
                    ),
                    why_it_matters=(
                        "When tonal color compresses too tightly, rich "
                        "arrangement differences start reading like the same idea repeated."
                    ),
                    suggested_action=(
                        "Audit spectral diversity and pitch-class spread "
                        "before clustering tracks into one sonic neighborhood."
                    ),
                ),
                _indicator(
                    "repetition-inflation",
                    "Repetition inflation",
                    score=min(mean(repetition_values), 1.0),
                    evidence=(
                        "Mean repetition ratio across the recent lane is "
                        f"{mean(repetition_values):.3f}."
                    ),
                    why_it_matters=(
                        "Loops are not inherently bad, but unchecked repetition "
                        "can make the model overvalue familiarity."
                    ),
                    suggested_action=(
                        "Keep loop-heavy segments in view and compare them "
                        "against more developmental sections."
                    ),
                ),
                _indicator(
                    "silence-padding-abuse",
                    "Silence-padding abuse",
                    score=min(mean(silence_values) * 1.35, 1.0),
                    evidence=(
                        f"Silence share sits at {mean(silence_values):.3f} "
                        "across recent segments."
                    ),
                    why_it_matters=(
                        "Padding can make a source look longer, calmer, or "
                        "cleaner than the useful content inside it."
                    ),
                    suggested_action=(
                        "Mark silence-heavy segments for direct review before "
                        "they influence benchmark timing."
                    ),
                ),
                _indicator(
                    "production-polish-bias",
                    "Production-polish bias",
                    score=max(0.0, min(1.0, 1.0 - mean(dynamic_ranges) / 0.65)),
                    evidence=(
                        "Median dynamic range in the recent lane is "
                        f"{median(dynamic_ranges):.3f}."
                    ),
                    why_it_matters=(
                        "Highly polished tracks can dominate if the system "
                        "learns compression sheen instead of musical difference."
                    ),
                    suggested_action=(
                        "Compare dynamic range distributions across sources "
                        "and keep looser recordings present in evaluation."
                    ),
                ),
                _indicator(
                    "regional-undercoverage",
                    "Regional undercoverage",
                    score=_regional_undercoverage_score(region_counts),
                    evidence=_share_evidence(
                        region_counts,
                        empty_text="No region metadata has been declared yet.",
                    ),
                    why_it_matters=(
                        "Regional absence is not neutral; it changes which "
                        "accents, scenes, and production habits ever become visible."
                    ),
                    suggested_action=(
                        "Add more regional manifests before treating the "
                        "warehouse as culturally representative."
                    ),
                ),
            ]
        )

    return MusicDriftReport(
        manifest_count=manifest_count,
        feature_run_count=feature_run_count,
        indicators=indicators,
    )


def build_music_change_proof(
    manifests: list[MusicTrackManifestRecord],
    runs: list[MusicFeatureWarehouseRun],
) -> MusicChangeProofResponse:
    if not runs:
        return MusicChangeProofResponse(
            manifest_count=len(manifests),
            feature_run_count=0,
            changes=[
                MusicChangeEvidence(
                    change_id="music-lane-empty",
                    title="No warehouse history yet",
                    entered_through="music_feature_extract",
                    summary="The warehouse is still waiting for its first persisted run.",
                    evidence=[
                        "Run the feature extractor on at least one manifest "
                        "to generate a comparative history."
                    ],
                    receipts=[],
                )
            ],
        )

    earliest = runs[-1]
    latest = runs[0]
    changes: list[MusicChangeEvidence] = []

    if latest.segment_count != earliest.segment_count:
        delta = latest.segment_count - earliest.segment_count
        changes.append(
            MusicChangeEvidence(
                change_id="segment-volume-shift",
                title="Segment volume shifted",
                entered_through="music_feature_extract",
                summary=(
                    f"Segment count moved from {earliest.segment_count} to {latest.segment_count} "
                    f"({delta:+d})."
                ),
                evidence=[
                    f"Earliest run: {earliest.run_id}",
                    f"Latest run: {latest.run_id}",
                    f"Partition labels: {earliest.partition_label} → {latest.partition_label}",
                ],
                receipts=[*earliest.receipts[:1], *latest.receipts[:1]],
            )
        )

    earliest_languages = Counter(earliest.languages)
    latest_languages = Counter(latest.languages)
    if latest_languages != earliest_languages:
        changes.append(
            MusicChangeEvidence(
                change_id="language-shift",
                title="Language mix changed",
                entered_through="music_manifest_register",
                summary=(
                    f"Language share moved from {dict(earliest_languages) or {'unlabeled': 1}} "
                    f"to {dict(latest_languages) or {'unlabeled': 1}}."
                ),
                evidence=[
                    f"Earliest manifest: {earliest.manifest_id}",
                    f"Latest manifest: {latest.manifest_id}",
                ],
                receipts=[*earliest.receipts[:1], *latest.receipts[:1]],
            )
        )

    entropy_delta = (
        latest.benchmark.average_entropy_score
        - earliest.benchmark.average_entropy_score
    )
    if abs(entropy_delta) >= 0.04:
        changes.append(
            MusicChangeEvidence(
                change_id="entropy-shift",
                title="Variation profile changed",
                entered_through="music_feature_extract",
                summary=(
                    f"Average entropy moved from {earliest.benchmark.average_entropy_score:.3f} "
                    f"to {latest.benchmark.average_entropy_score:.3f}."
                ),
                evidence=[
                    f"Change delta: {entropy_delta:+.3f}",
                    f"Latest feature table: {latest.feature_table_path}",
                ],
                receipts=[*earliest.receipts[:1], *latest.receipts[:1]],
            )
        )

    if not changes:
        changes.append(
            MusicChangeEvidence(
                change_id="steady-state",
                title="The recent warehouse posture is steady",
                entered_through="music_feature_extract",
                summary=(
                    "The latest run did not materially diverge from the "
                    "earliest recorded comparison lane."
                ),
                evidence=[
                    f"Earliest run: {earliest.run_id}",
                    f"Latest run: {latest.run_id}",
                ],
                receipts=[*earliest.receipts[:1], *latest.receipts[:1]],
            )
        )

    return MusicChangeProofResponse(
        manifest_count=len(manifests),
        feature_run_count=len(runs),
        earliest_run_id=earliest.run_id,
        latest_run_id=latest.run_id,
        changes=changes,
    )


def build_music_snapshot(
    *,
    overview,
    drift: MusicDriftReport,
    change_proof: MusicChangeProofResponse,
    segment_slice,
    alignment_preview: TemporalAlignmentResponse,
) -> MusicWarehouseSnapshot:
    return MusicWarehouseSnapshot(
        overview=overview,
        drift=drift,
        change_proof=change_proof,
        segment_slice=segment_slice,
        alignment_preview=alignment_preview,
    )


def _indicator(
    indicator_id: str,
    label: str,
    *,
    score: float,
    evidence: str,
    why_it_matters: str,
    suggested_action: str,
) -> MusicDriftIndicator:
    if score >= 0.7:
        status = "elevated"
    elif score >= 0.38:
        status = "watch"
    else:
        status = "steady"
    return MusicDriftIndicator(
        indicator_id=indicator_id,
        label=label,
        status=status,
        score=max(0.0, min(score, 1.0)),
        evidence=evidence,
        why_it_matters=why_it_matters,
        suggested_action=suggested_action,
    )


def _quality_flags(*, segment: MusicSegmentInput, feature) -> list[str]:
    flags: list[str] = []
    if feature is None:
        return ["missing-feature-vector"]
    if feature.silence_ratio >= 0.5:
        flags.append("silence-heavy")
    if feature.repetition_ratio >= 0.68:
        flags.append("repetition-heavy")
    if feature.entropy_score <= 0.2:
        flags.append("variation-thin")
    if segment.transcript_excerpt.strip() == "":
        flags.append("missing-transcript-link")
    if (
        not segment.attributes.get("video_window_start_ms")
        and not segment.attributes.get("frame_ref")
    ):
        flags.append("missing-visual-link")
    return flags


def _share_evidence(counter: Counter, *, empty_text: str) -> str:
    if not counter:
        return empty_text
    top_label, top_count = counter.most_common(1)[0]
    total = sum(counter.values()) or 1
    return (
        f"{top_label} currently accounts for "
        f"{(top_count / total) * 100:.1f}% of the declared coverage."
    )


def _top_share(counter: Counter) -> float:
    if not counter:
        return 0.0
    total = sum(counter.values()) or 1
    return counter.most_common(1)[0][1] / total


def _regional_undercoverage_score(counter: Counter) -> float:
    if not counter:
        return 1.0
    total = sum(counter.values()) or 1
    expected_minimum_share = 1.0 / max(len(counter), 1)
    weakest_share = min(count / total for count in counter.values())
    return max(0.0, min(1.0, (expected_minimum_share - weakest_share) * len(counter)))


def _optional_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
