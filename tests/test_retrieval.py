from advanced_multimodal_ai.config import Settings
from advanced_multimodal_ai.contracts import (
    RetrievalQueryRequest,
    RetrievalRecord,
    RetrievalUpsertRequest,
)
from advanced_multimodal_ai.retrieval import create_vector_index


def test_memory_vector_index_returns_ranked_matches():
    index = create_vector_index(Settings())
    index.upsert(
        RetrievalUpsertRequest(
            records=[
                RetrievalRecord(
                    record_id="a",
                    modality="text",
                    vector=[1.0, 0.0, 0.0],
                    metadata={"topic": "ml"},
                ),
                RetrievalRecord(
                    record_id="b",
                    modality="text",
                    vector=[0.0, 1.0, 0.0],
                    metadata={"topic": "vision"},
                ),
            ]
        )
    )
    matches = index.query(
        RetrievalQueryRequest(modality="text", vector=[0.9, 0.1, 0.0], top_k=2, metadata_filter={})
    )
    assert matches[0].record_id == "a"
    assert matches[0].score >= matches[1].score


def test_memory_vector_index_rejects_dimension_mismatch():
    index = create_vector_index(Settings())
    index.upsert(
        RetrievalUpsertRequest(
            records=[
                RetrievalRecord(
                    record_id="seed",
                    modality="text",
                    vector=[1.0, 0.0, 0.0],
                    metadata={},
                )
            ]
        )
    )
    try:
        index.upsert(
            RetrievalUpsertRequest(
                records=[
                    RetrievalRecord(
                        record_id="broken",
                        modality="text",
                        vector=[1.0, 0.0],
                        metadata={},
                    )
                ]
            )
        )
    except ValueError as error:
        assert "expects vectors of width" in str(error)
    else:  # pragma: no cover - the exception path is the assertion
        raise AssertionError("dimension mismatch should raise a ValueError")
