from __future__ import annotations

from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Iterable

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from .contracts import (
    MusicFeatureExtractionRequest,
    MusicFeatureVector,
    MusicSegmentInput,
    MusicTrackManifestRecord,
    MusicWarehouseBenchmark,
)
from .signal_math import normalized_entropy

PITCH_CLASS_LABELS = [
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
]


def build_music_feature_rows(
    manifest: MusicTrackManifestRecord,
    request: MusicFeatureExtractionRequest,
) -> tuple[list[dict[str, object]], list[MusicFeatureVector], MusicWarehouseBenchmark]:
    feature_vectors: list[MusicFeatureVector] = []
    row_dicts: list[dict[str, object]] = []

    extraction_started = _now_counter()
    for segment in request.segments:
        vector = extract_segment_features(segment)
        feature_vectors.append(vector)
        row_dicts.append(_feature_row(manifest, request.partition_label, vector))
    extraction_elapsed = _elapsed_ms(extraction_started)

    average_entropy = (
        float(sum(item.entropy_score for item in feature_vectors) / len(feature_vectors))
        if feature_vectors
        else 0.0
    )
    average_tempo = (
        float(sum(item.tempo_proxy_bpm for item in feature_vectors) / len(feature_vectors))
        if feature_vectors
        else 0.0
    )
    average_key_clarity = (
        float(sum(item.key_clarity for item in feature_vectors) / len(feature_vectors))
        if feature_vectors
        else 0.0
    )

    benchmark = MusicWarehouseBenchmark(
        extraction_ms=extraction_elapsed,
        persist_ms=0.0,
        total_ms=extraction_elapsed,
        segment_count=len(feature_vectors),
        bytes_written=0,
        rows_per_second=float((len(feature_vectors) / extraction_elapsed) * 1000.0)
        if extraction_elapsed
        else 0.0,
        average_entropy_score=average_entropy,
        average_tempo_proxy_bpm=average_tempo,
        average_key_clarity=average_key_clarity,
    )
    return row_dicts, feature_vectors, benchmark


def persist_feature_rows(
    rows: list[dict[str, object]],
    output_path: Path,
    benchmark: MusicWarehouseBenchmark,
) -> MusicWarehouseBenchmark:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    persist_started = _now_counter()
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, output_path)
    persist_elapsed = _elapsed_ms(persist_started)
    bytes_written = output_path.stat().st_size if output_path.exists() else 0
    return benchmark.model_copy(
        update={
            "persist_ms": persist_elapsed,
            "total_ms": benchmark.extraction_ms + persist_elapsed,
            "bytes_written": bytes_written,
        }
    )


def summarize_music_findings(
    manifests: Iterable[MusicTrackManifestRecord],
    runs: Iterable,
) -> tuple[dict[str, int], dict[str, int], list[str], int]:
    manifest_list = list(manifests)
    run_list = list(runs)
    genre_counts = Counter(
        genre
        for manifest in manifest_list
        for genre in manifest.genres
        if genre.strip()
    )
    language_counts = Counter(
        language
        for manifest in manifest_list
        for language in manifest.languages
        if language.strip()
    )
    total_segments = sum(getattr(run, "segment_count", 0) for run in run_list)

    findings: list[str] = []
    if run_list:
        average_entropy = sum(
            run.benchmark.average_entropy_score for run in run_list
        ) / len(run_list)
        average_clarity = sum(
            run.benchmark.average_key_clarity for run in run_list
        ) / len(run_list)
        if average_entropy < 0.32:
            findings.append(
                "The current sound field is still structurally narrow. "
                "More contrast between sections would make drift easier to catch."
            )
        if average_clarity > 0.72:
            findings.append(
                "Pitch energy is concentrating around a small tonal center. "
                "That can be musically intentional, but it is also where "
                "homogenized training sets hide."
            )
        if not findings:
            findings.append(
                "Recent runs show a healthier spread of motion, energy, and "
                "pitch weight across segments."
            )
    else:
        findings.append(
            "No persisted music feature runs exist yet. The lane is ready, "
            "but it still needs witnessed inputs."
        )

    return dict(genre_counts), dict(language_counts), findings, total_segments


def extract_segment_features(segment: MusicSegmentInput) -> MusicFeatureVector:
    signal = _signal_from_segment(segment)
    duration_ms = max(segment.end_ms - segment.start_ms, 1)
    source_signal = "waveform" if segment.waveform else "energy_trace"
    sample_rate_hz = segment.sample_rate_hz
    peak = float(np.max(np.abs(signal))) if signal.size else 0.0
    rms_energy = float(np.sqrt(np.mean(np.square(signal)))) if signal.size else 0.0
    silence_threshold = peak * 0.03
    silence_ratio = (
        float(np.mean(np.abs(signal) <= silence_threshold)) if peak > 0.0 else 1.0
    )

    zero_crossings = 0.0
    if signal.size > 1:
        zero_crossings = float(np.mean(np.diff(np.signbit(signal)).astype(np.float32) != 0))

    abs_signal = np.abs(signal)
    dynamic_range = (
        float(np.percentile(abs_signal, 95) - np.percentile(abs_signal, 5))
        if signal.size
        else 0.0
    )
    crest_factor = float(peak / rms_energy) if rms_energy > 1e-9 else 0.0
    entropy_score = float(normalized_entropy(signal))

    spectra, freqs = _spectral_frames(signal, sample_rate_hz)
    mean_spectrum = spectra.mean(axis=0) if spectra.size else np.zeros(1, dtype=np.float32)
    spectral_sum = float(np.sum(mean_spectrum)) or 1.0
    spectral_centroid = float(np.sum(freqs * mean_spectrum) / spectral_sum)
    spectral_bandwidth = float(
        np.sqrt(np.sum(((freqs - spectral_centroid) ** 2) * mean_spectrum) / spectral_sum)
    )
    cumulative = np.cumsum(mean_spectrum)
    rolloff_threshold = cumulative[-1] * 0.85 if cumulative.size else 0.0
    rolloff_index = int(np.searchsorted(cumulative, rolloff_threshold))
    spectral_rolloff = float(freqs[min(rolloff_index, len(freqs) - 1)]) if freqs.size else 0.0

    spectral_flux_series = _spectral_flux(spectra)
    spectral_flux = float(np.mean(spectral_flux_series)) if spectral_flux_series.size else 0.0
    onset_indices = _onset_indices(spectral_flux_series)
    duration_seconds = max(duration_ms / 1000.0, 1e-6)
    onset_density = float(len(onset_indices) / duration_seconds)
    tempo_proxy = _tempo_proxy_bpm(onset_indices, signal.size, sample_rate_hz)
    repetition_ratio = _repetition_ratio(signal)
    chroma = _pitch_class_profile(mean_spectrum, freqs)
    dominant_pitch_class = PITCH_CLASS_LABELS[int(np.argmax(chroma))] if chroma.size else "C"
    key_clarity = float(np.max(chroma)) if chroma.size else 0.0

    notes: list[str] = []
    if silence_ratio > 0.48:
        notes.append("This section holds a large silence share and may need denser corroboration.")
    if entropy_score < 0.18:
        notes.append("Variation is low. The segment may be looping or over-compressed.")
    if spectral_flux < 0.015:
        notes.append(
            "Spectral movement is restrained, so change detection may "
            "under-read transitions."
        )

    return MusicFeatureVector(
        segment_id=segment.segment_id,
        start_ms=segment.start_ms,
        end_ms=segment.end_ms,
        label=segment.label,
        transcript_excerpt=segment.transcript_excerpt,
        speaker=segment.speaker,
        source_signal=source_signal,
        sample_count=int(signal.size),
        duration_ms=duration_ms,
        rms_energy=rms_energy,
        silence_ratio=silence_ratio,
        zero_crossing_rate=zero_crossings,
        dynamic_range=dynamic_range,
        crest_factor=crest_factor,
        entropy_score=entropy_score,
        spectral_centroid_hz=spectral_centroid,
        spectral_bandwidth_hz=spectral_bandwidth,
        spectral_rolloff_hz=spectral_rolloff,
        spectral_flux=spectral_flux,
        onset_density=onset_density,
        tempo_proxy_bpm=tempo_proxy,
        repetition_ratio=repetition_ratio,
        key_clarity=key_clarity,
        dominant_pitch_class=dominant_pitch_class,
        pitch_class_profile=chroma.tolist(),
        notes=notes,
    )


def _feature_row(
    manifest: MusicTrackManifestRecord,
    partition_label: str,
    vector: MusicFeatureVector,
) -> dict[str, object]:
    row = {
        "manifest_id": manifest.manifest_id,
        "track_name": manifest.track_name,
        "owner": manifest.owner,
        "source_uri": manifest.source_uri,
        "source_kind": manifest.source_kind,
        "partition_label": partition_label,
        "segment_id": vector.segment_id,
        "start_ms": vector.start_ms,
        "end_ms": vector.end_ms,
        "label": vector.label,
        "speaker": vector.speaker,
        "source_signal": vector.source_signal,
        "sample_count": vector.sample_count,
        "duration_ms": vector.duration_ms,
        "rms_energy": vector.rms_energy,
        "silence_ratio": vector.silence_ratio,
        "zero_crossing_rate": vector.zero_crossing_rate,
        "dynamic_range": vector.dynamic_range,
        "crest_factor": vector.crest_factor,
        "entropy_score": vector.entropy_score,
        "spectral_centroid_hz": vector.spectral_centroid_hz,
        "spectral_bandwidth_hz": vector.spectral_bandwidth_hz,
        "spectral_rolloff_hz": vector.spectral_rolloff_hz,
        "spectral_flux": vector.spectral_flux,
        "onset_density": vector.onset_density,
        "tempo_proxy_bpm": vector.tempo_proxy_bpm,
        "repetition_ratio": vector.repetition_ratio,
        "key_clarity": vector.key_clarity,
        "dominant_pitch_class": vector.dominant_pitch_class,
    }
    for index, value in enumerate(vector.pitch_class_profile):
        row[f"pitch_class_{PITCH_CLASS_LABELS[index].replace('#', 'sharp').lower()}"] = value
    return row


def _signal_from_segment(segment: MusicSegmentInput) -> np.ndarray:
    values = segment.waveform if segment.waveform else segment.energy_trace
    signal = np.asarray(values, dtype=np.float32).reshape(-1)
    if not signal.size:
        return np.zeros(32, dtype=np.float32)
    if signal.size < 32:
        signal = np.pad(signal, (0, 32 - signal.size), mode="edge")
    return signal


def _spectral_frames(signal: np.ndarray, sample_rate_hz: int) -> tuple[np.ndarray, np.ndarray]:
    frame_length = min(512, max(64, _nearest_power_of_two(signal.size // 4 or signal.size)))
    if signal.size < frame_length:
        signal = np.pad(signal, (0, frame_length - signal.size), mode="constant")
    hop = max(frame_length // 2, 1)
    frames = []
    for start in range(0, max(signal.size - frame_length + 1, 1), hop):
        frame = signal[start : start + frame_length]
        if frame.size < frame_length:
            frame = np.pad(frame, (0, frame_length - frame.size), mode="constant")
        window = np.hanning(frame_length).astype(np.float32)
        frames.append(np.abs(np.fft.rfft(frame * window)))
    if not frames:
        frames.append(np.abs(np.fft.rfft(signal[:frame_length])))
    spectra = np.vstack(frames).astype(np.float32)
    freqs = np.fft.rfftfreq(frame_length, d=1.0 / float(sample_rate_hz)).astype(np.float32)
    return spectra, freqs


def _nearest_power_of_two(value: int) -> int:
    candidate = 1
    while candidate < max(value, 1):
        candidate <<= 1
    return candidate


def _spectral_flux(spectra: np.ndarray) -> np.ndarray:
    if spectra.shape[0] < 2:
        return np.zeros(1, dtype=np.float32)
    diffs = np.diff(spectra, axis=0)
    positive = np.maximum(diffs, 0.0)
    flux = np.sqrt(np.mean(np.square(positive), axis=1))
    return flux.astype(np.float32)


def _onset_indices(flux: np.ndarray) -> np.ndarray:
    if flux.size == 0:
        return np.array([], dtype=np.int32)
    threshold = float(np.mean(flux) + np.std(flux) * 0.5)
    peaks = []
    for index in range(1, len(flux) - 1):
        if (
            flux[index] >= threshold
            and flux[index] >= flux[index - 1]
            and flux[index] >= flux[index + 1]
        ):
            peaks.append(index)
    return np.asarray(peaks, dtype=np.int32)


def _tempo_proxy_bpm(onset_indices: np.ndarray, sample_count: int, sample_rate_hz: int) -> float:
    if onset_indices.size < 2:
        return 0.0
    frame_length = min(512, max(64, _nearest_power_of_two(sample_count // 4 or sample_count)))
    hop_seconds = (frame_length // 2) / float(sample_rate_hz)
    intervals = np.diff(onset_indices) * hop_seconds
    intervals = intervals[intervals > 1e-6]
    if intervals.size == 0:
        return 0.0
    bpm = float(60.0 / np.median(intervals))
    return max(0.0, min(bpm, 320.0))


def _repetition_ratio(signal: np.ndarray) -> float:
    if signal.size < 8:
        return 0.0
    centered = signal - float(np.mean(signal))
    denominator = float(np.sum(np.square(centered)))
    if denominator <= 1e-8:
        return 1.0
    autocorr = np.correlate(centered, centered, mode="full")[signal.size - 1 :]
    if autocorr.size < 4:
        return 0.0
    candidate = autocorr[1 : max(2, signal.size // 2)]
    if candidate.size == 0:
        return 0.0
    ratio = float(np.max(candidate) / autocorr[0])
    return max(0.0, min(ratio, 1.0))


def _pitch_class_profile(spectrum: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    chroma = np.zeros(12, dtype=np.float32)
    if not spectrum.size or not freqs.size:
        return chroma
    valid = freqs >= 27.5
    if not np.any(valid):
        return chroma
    active_freqs = freqs[valid]
    active_spectrum = spectrum[valid]
    midi = np.rint(69 + 12 * np.log2(active_freqs / 440.0)).astype(np.int32)
    pitch_classes = np.mod(midi, 12)
    for pitch_class in range(12):
        chroma[pitch_class] = float(np.sum(active_spectrum[pitch_classes == pitch_class]))
    total = float(np.sum(chroma))
    if total <= 1e-9:
        return chroma
    return chroma / total


def _now_counter() -> float:
    return perf_counter()


def _elapsed_ms(start_value: float) -> float:
    return max((perf_counter() - start_value) * 1000.0, 0.0)
