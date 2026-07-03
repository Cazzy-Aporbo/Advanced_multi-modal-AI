from __future__ import annotations

from typing import Any

from hypothesis import given
from hypothesis import settings as hsettings
from hypothesis import strategies as st
from pydantic import ValidationError

from advanced_multimodal_ai.config import Settings
from advanced_multimodal_ai.connectors import build_pipeline_events_from_rows
from advanced_multimodal_ai.contracts import (
    ConnectorModalityMapping,
    InferenceRequest,
    TensorPayload,
)
from advanced_multimodal_ai.tensor_guard import build_tensor_intercept_response

FINITE_FLOATS = st.floats(
    min_value=-1.0e6,
    max_value=1.0e6,
    allow_nan=False,
    allow_infinity=False,
    width=32,
)
MODALITIES = ["text", "image", "audio", "video", "sensor", "tabular"]


@st.composite
def tensor_payload_case(draw) -> dict[str, Any]:
    batch_size = draw(st.integers(min_value=1, max_value=3))
    feature_width = draw(st.integers(min_value=1, max_value=16))
    total = batch_size * feature_width
    values = draw(st.lists(FINITE_FLOATS, min_size=total, max_size=total))
    return {
        "shape": [batch_size, feature_width],
        "values": values,
        "dtype": "float32",
    }


@st.composite
def mismatched_tensor_payload_case(draw) -> dict[str, Any]:
    batch_size = draw(st.integers(min_value=1, max_value=3))
    feature_width = draw(st.integers(min_value=1, max_value=16))
    expected = batch_size * feature_width
    offset = draw(st.integers(min_value=1, max_value=4))
    too_many = draw(st.booleans())
    actual = expected + offset if too_many else max(1, expected - offset)
    values = draw(st.lists(FINITE_FLOATS, min_size=actual, max_size=actual))
    return {
        "shape": [batch_size, feature_width],
        "values": values,
        "dtype": "float32",
    }


@st.composite
def inference_request_case(draw) -> InferenceRequest:
    batch_size = draw(st.integers(min_value=1, max_value=3))
    modality_names = draw(
        st.lists(
            st.sampled_from(MODALITIES),
            min_size=1,
            max_size=3,
            unique=True,
        )
    )
    modalities: dict[str, TensorPayload] = {}
    for modality_name in modality_names:
        feature_width = draw(st.integers(min_value=2, max_value=24))
        total = batch_size * feature_width
        values = draw(st.lists(FINITE_FLOATS, min_size=total, max_size=total))
        modalities[modality_name] = TensorPayload(
            shape=[batch_size, feature_width],
            values=values,
        )

    restricted_modalities = draw(
        st.lists(
            st.sampled_from(modality_names),
            unique=True,
            max_size=len(modality_names),
        )
    )
    request = InferenceRequest(
        model_id="adaptive_transformer",
        runtime_mode=draw(st.sampled_from(["contract", "research"])),
        target=draw(st.sampled_from(["embedding", "classification", "retrieval"])),
        num_classes=draw(st.one_of(st.none(), st.integers(min_value=2, max_value=8))),
        modalities=modalities,
        metadata={
            "request_id": draw(st.text(min_size=1, max_size=24)),
            "restricted_modalities": restricted_modalities,
            "block_tensor_intercept": draw(st.booleans()),
            "max_intercept_risk": draw(
                st.floats(
                    min_value=0.1,
                    max_value=0.95,
                    allow_nan=False,
                    allow_infinity=False,
                )
            ),
        },
    )
    return request


@st.composite
def connector_rows_case(draw) -> list[dict[str, Any]]:
    row_strategy = st.fixed_dictionaries(
        {
            "pk": st.text(
                alphabet=st.characters(
                    whitelist_categories=("Ll", "Lu", "Nd"),
                    min_codepoint=48,
                    max_codepoint=122,
                ),
                min_size=1,
                max_size=12,
            )
        },
        optional={
            "left": st.one_of(FINITE_FLOATS, st.none()),
            "right": st.one_of(FINITE_FLOATS, st.none()),
            "intensity": st.one_of(FINITE_FLOATS, st.none()),
        },
    )
    return draw(st.lists(row_strategy, min_size=1, max_size=24))


@given(payload=tensor_payload_case())
@hsettings(max_examples=60, deadline=None)
def test_tensor_payload_round_trips_valid_lengths(payload: dict[str, Any]) -> None:
    record = TensorPayload.model_validate(payload)
    assert record.shape == payload["shape"]
    assert len(record.values) == len(payload["values"])


@given(payload=mismatched_tensor_payload_case())
@hsettings(max_examples=60, deadline=None)
def test_tensor_payload_rejects_mismatched_lengths(payload: dict[str, Any]) -> None:
    expected = payload["shape"][0] * payload["shape"][1]
    if expected == len(payload["values"]):
        return
    try:
        TensorPayload.model_validate(payload)
    except ValidationError:
        return
    raise AssertionError("TensorPayload accepted a mismatched flattened value count")


@given(request=inference_request_case())
@hsettings(max_examples=45, deadline=None)
def test_tensor_intercept_response_stays_bounded_under_varied_inputs(
    request: InferenceRequest,
) -> None:
    response = build_tensor_intercept_response(request, Settings())
    assert len(response.intercept_profiles) == len(request.modalities)
    assert response.policy_mode in {"observe", "enforce"}
    for profile in response.intercept_profiles:
        assert 0.0 <= profile.entropy_score <= 1.0
        assert 0.0 <= profile.spatial_frequency <= 1.0
        assert 0.0 <= profile.saturation_ratio <= 1.0
        assert 0.0 <= profile.zero_ratio <= 1.0
        assert 0.0 <= profile.risk_score <= 1.0
        assert profile.status in {"ok", "watch", "fail"}
    if response.blocked:
        assert response.policy_mode == "enforce"
        assert response.triggered_modalities
    assert set(response.triggered_modalities).issubset(set(request.modalities.keys()))


@given(rows=connector_rows_case())
@hsettings(max_examples=50, deadline=None)
def test_connector_pipeline_mapping_drops_invalid_rows_without_partial_events(
    rows: list[dict[str, Any]],
) -> None:
    mappings = [
        ConnectorModalityMapping(
            modality="tabular",
            feature_fields=["left", "right"],
            source="pair-shape",
        ),
        ConnectorModalityMapping(
            modality="sensor",
            feature_fields=["right", "intensity"],
            source="energy-shape",
        ),
    ]

    events, dropped_rows = build_pipeline_events_from_rows(
        rows=rows,
        mappings=mappings,
        partition_key_field="pk",
        drop_invalid_rows=True,
    )

    def _valid_row(row: dict[str, Any]) -> bool:
        return all(
            row.get(field) is not None
            for field in {"left", "right", "intensity"}
        )

    valid_rows = sum(1 for row in rows if _valid_row(row))
    assert dropped_rows == len(rows) - valid_rows
    assert len(events) == valid_rows * len(mappings)
    for event in events:
        assert event.tensor.shape == [1, 2]
        assert len(event.tensor.values) == 2
