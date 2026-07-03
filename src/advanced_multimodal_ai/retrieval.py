from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from .config import Settings
from .contracts import (
    RetrievalMatch,
    RetrievalQueryRequest,
    RetrievalRecord,
    RetrievalUpsertRequest,
)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qdrant_models
except Exception:  # pragma: no cover - optional dependency path
    QdrantClient = None
    qdrant_models = None


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = np.linalg.norm(left)
    right_norm = np.linalg.norm(right)
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def _matches_filter(metadata: Dict[str, object], expected: Dict[str, object]) -> bool:
    return all(metadata.get(key) == value for key, value in expected.items())


@dataclass
class InMemoryVectorIndex:
    records: Dict[str, RetrievalRecord]
    vector_dimensions: Dict[str, int]

    def __init__(self) -> None:
        self.records = {}
        self.vector_dimensions = {}

    @property
    def backend(self) -> str:
        return "memory"

    def upsert(self, request: RetrievalUpsertRequest) -> int:
        for record in request.records:
            dimension = len(record.vector)
            existing_dimension = self.vector_dimensions.get(record.modality)
            if existing_dimension is not None and existing_dimension != dimension:
                raise ValueError(
                    f"Modality '{record.modality}' expects vectors of width "
                    f"{existing_dimension}, received {dimension}"
                )
            self.records[record.record_id] = record
            self.vector_dimensions[record.modality] = dimension
        return len(request.records)

    def query(self, request: RetrievalQueryRequest) -> List[RetrievalMatch]:
        query_vector = np.asarray(request.vector, dtype=np.float32)
        expected_dimension = self.vector_dimensions.get(request.modality)
        if expected_dimension is not None and expected_dimension != len(request.vector):
            raise ValueError(
                f"Query vector for modality '{request.modality}' must have width "
                f"{expected_dimension}, received {len(request.vector)}"
            )
        matches: List[RetrievalMatch] = []
        for record in self.records.values():
            if record.modality != request.modality:
                continue
            if request.metadata_filter and not _matches_filter(
                record.metadata, request.metadata_filter
            ):
                continue
            score = _cosine_similarity(query_vector, np.asarray(record.vector, dtype=np.float32))
            matches.append(
                RetrievalMatch(
                    record_id=record.record_id,
                    modality=record.modality,
                    score=score,
                    metadata=record.metadata,
                )
            )
        matches.sort(key=lambda item: item.score, reverse=True)
        return matches[: request.top_k]


class QdrantVectorIndex:
    def __init__(self, settings: Settings) -> None:
        if QdrantClient is None or qdrant_models is None:
            raise RuntimeError("qdrant-client is not available in this environment")
        self.settings = settings
        self.client = QdrantClient(url=settings.qdrant_url)
        self._ensure_collection()

    @property
    def backend(self) -> str:
        return "qdrant"

    def _ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        if any(collection.name == self.settings.qdrant_collection for collection in collections):
            return
        self.client.create_collection(
            collection_name=self.settings.qdrant_collection,
            vectors_config=qdrant_models.VectorParams(
                size=self.settings.retrieval_vector_dim,
                distance=qdrant_models.Distance.COSINE,
            ),
        )

    def upsert(self, request: RetrievalUpsertRequest) -> int:
        points = []
        for record in request.records:
            vector = np.asarray(record.vector, dtype=np.float32)
            if len(vector) != self.settings.retrieval_vector_dim:
                raise ValueError(
                    "The current Qdrant retrieval lane expects vectors of width "
                    f"{self.settings.retrieval_vector_dim} that match the configured "
                    "signature surface."
                )
            points.append(
                qdrant_models.PointStruct(
                    id=record.record_id,
                    vector=vector.tolist(),
                    payload={
                        "record_id": record.record_id,
                        "modality": record.modality,
                        **record.metadata,
                    },
                )
            )
        self.client.upsert(collection_name=self.settings.qdrant_collection, points=points)
        return len(points)

    def query(self, request: RetrievalQueryRequest) -> List[RetrievalMatch]:
        if len(request.vector) != self.settings.retrieval_vector_dim:
            raise ValueError(
                "The current Qdrant retrieval lane expects vectors of width "
                f"{self.settings.retrieval_vector_dim} that match the configured "
                "signature surface."
            )
        results = self.client.search(
            collection_name=self.settings.qdrant_collection,
            query_vector=request.vector,
            limit=request.top_k,
        )
        matches: List[RetrievalMatch] = []
        for result in results:
            payload = result.payload or {}
            if payload.get("modality") != request.modality:
                continue
            if request.metadata_filter and not _matches_filter(payload, request.metadata_filter):
                continue
            matches.append(
                RetrievalMatch(
                    record_id=str(payload.get("record_id", result.id)),
                    modality=request.modality,
                    score=float(result.score),
                    metadata={
                        key: value
                        for key, value in payload.items()
                        if key not in {"record_id", "modality"}
                    },
                )
            )
        return matches


def create_vector_index(settings: Settings) -> InMemoryVectorIndex | QdrantVectorIndex:
    if settings.retrieval_backend.lower() == "qdrant":
        return QdrantVectorIndex(settings)
    return InMemoryVectorIndex()
