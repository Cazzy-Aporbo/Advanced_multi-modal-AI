from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pyarrow as pa
import pyarrow.parquet as pq

from .contracts import (
    MusicEmbeddingRecord,
    MusicExtractionReceipt,
    MusicFeatureVector,
    MusicTrackManifestRecord,
    RetrievalRecord,
    RetrievalUpsertRequest,
)

EMBEDDING_MODEL_NAME = "amai.audio.segment.signature.v1"
EMBEDDING_FIELDS = [
    "rms_energy",
    "silence_ratio",
    "entropy_score",
    "spectral_centroid_hz",
    "spectral_flux",
    "tempo_proxy_bpm",
    "repetition_ratio",
    "key_clarity",
]


def embedding_contract_hash() -> str:
    payload = json.dumps(
        {
            "model": EMBEDDING_MODEL_NAME,
            "fields": EMBEDDING_FIELDS,
            "vector_dim": len(EMBEDDING_FIELDS),
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_embedding_records(
    *,
    run_id: str,
    manifest: MusicTrackManifestRecord,
    vectors: list[MusicFeatureVector],
) -> list[MusicEmbeddingRecord]:
    contract_hash = embedding_contract_hash()
    records: list[MusicEmbeddingRecord] = []
    for vector in vectors:
        records.append(
            MusicEmbeddingRecord(
                record_id=str(uuid4()),
                run_id=run_id,
                manifest_id=manifest.manifest_id,
                segment_id=vector.segment_id,
                model_name=EMBEDDING_MODEL_NAME,
                contract_hash=contract_hash,
                vector=_vector_from_features(vector),
                metadata={
                    "track_name": manifest.track_name,
                    "owner": manifest.owner,
                    "genres": manifest.genres,
                    "languages": manifest.languages,
                    "segment_label": vector.label,
                    "start_ms": vector.start_ms,
                    "end_ms": vector.end_ms,
                },
            )
        )
    return records


def persist_embedding_records(
    records: list[MusicEmbeddingRecord],
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "record_id": item.record_id,
            "run_id": item.run_id,
            "manifest_id": item.manifest_id,
            "segment_id": item.segment_id,
            "model_name": item.model_name,
            "contract_hash": item.contract_hash,
            **{f"vector_{index}": value for index, value in enumerate(item.vector)},
            "metadata_json": json.dumps(item.metadata, sort_keys=True),
        }
        for item in records
    ]
    pq.write_table(pa.Table.from_pylist(rows), output_path)
    return output_path


def retrieval_request_from_embeddings(
    records: list[MusicEmbeddingRecord],
) -> RetrievalUpsertRequest:
    return RetrievalUpsertRequest(
        records=[
            RetrievalRecord(
                record_id=item.record_id,
                modality="audio",
                vector=item.vector,
                metadata={
                    **item.metadata,
                    "run_id": item.run_id,
                    "manifest_id": item.manifest_id,
                    "segment_id": item.segment_id,
                    "model_name": item.model_name,
                    "contract_hash": item.contract_hash,
                },
            )
            for item in records
        ]
    )


def build_music_receipt(
    *,
    manifest: MusicTrackManifestRecord,
    extractor_version: str,
    feature_schema_version: str,
    output_path: Path,
    embedding_model: str,
    contract_hash: str,
) -> MusicExtractionReceipt:
    output_bytes = output_path.stat().st_size if output_path.exists() else 0
    output_sha256 = _sha256_file(output_path) if output_path.exists() else ""
    source_sha256 = manifest.content_sha256 or manifest.source_fingerprint
    return MusicExtractionReceipt(
        source_sha256=source_sha256,
        source_fingerprint=manifest.source_fingerprint,
        extractor_version=extractor_version,
        feature_schema_version=feature_schema_version,
        embedding_model=embedding_model,
        contract_hash=contract_hash,
        output_path=str(output_path),
        output_sha256=output_sha256,
        output_bytes=output_bytes,
    )


def _vector_from_features(vector: MusicFeatureVector) -> list[float]:
    return [
        round(float(vector.rms_energy), 6),
        round(float(vector.silence_ratio), 6),
        round(float(vector.entropy_score), 6),
        round(min(float(vector.spectral_centroid_hz) / 8_000.0, 1.0), 6),
        round(min(float(vector.spectral_flux) * 4.0, 1.0), 6),
        round(min(float(vector.tempo_proxy_bpm) / 240.0, 1.0), 6),
        round(float(vector.repetition_ratio), 6),
        round(float(vector.key_clarity), 6),
    ]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
