from __future__ import annotations

import csv
import json
import os
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import pyarrow as pa
import pyarrow.parquet as pq

try:
    import boto3
except Exception:  # pragma: no cover - optional dependency path
    boto3 = None

from .contracts import (
    ConnectorBenchmark,
    ConnectorConfig,
    ConnectorModalityMapping,
    DatasetField,
    PipelineEvent,
    TensorPayload,
)


def materialize_connector_rows(
    connector: ConnectorConfig,
    limit: int,
) -> tuple[list[dict[str, Any]], ConnectorBenchmark]:
    fetch_started = perf_counter()
    raw_bytes = _read_connector_bytes(connector)
    fetch_elapsed = (perf_counter() - fetch_started) * 1000

    parse_started = perf_counter()
    rows = _parse_rows(connector, raw_bytes)
    trimmed = rows[:limit]
    parse_elapsed = (perf_counter() - parse_started) * 1000
    total_elapsed = fetch_elapsed + parse_elapsed

    benchmark = ConnectorBenchmark(
        fetch_ms=float(fetch_elapsed),
        parse_ms=float(parse_elapsed),
        total_ms=float(total_elapsed),
        record_count=len(trimmed),
        bytes_read=len(raw_bytes),
        rows_per_second=float((len(trimmed) / total_elapsed) * 1000) if total_elapsed else 0.0,
    )
    return trimmed, benchmark


def infer_dataset_fields(rows: list[dict[str, Any]]) -> list[DatasetField]:
    if not rows:
        return []

    ordered_names: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for name in row:
            if name not in seen:
                seen.add(name)
                ordered_names.append(name)

    fields: list[DatasetField] = []
    for name in ordered_names:
        values = [row.get(name) for row in rows]
        nullable = any(_is_missing(value) for value in values)
        dtype = _infer_dtype(values)
        fields.append(
            DatasetField(
                name=name,
                dtype=dtype,
                nullable=nullable,
                semantic_role=_semantic_role(name),
            )
        )
    return fields


def build_pipeline_events_from_rows(
    rows: list[dict[str, Any]],
    mappings: list[ConnectorModalityMapping],
    partition_key_field: str,
    drop_invalid_rows: bool,
) -> tuple[list[PipelineEvent], int]:
    events: list[PipelineEvent] = []
    dropped_rows = 0

    for row_index, row in enumerate(rows):
        row_failed = False
        staged: list[PipelineEvent] = []
        for mapping in mappings:
            try:
                vector = [_coerce_float(row[field]) for field in mapping.feature_fields]
            except (KeyError, TypeError, ValueError):
                row_failed = True
                if drop_invalid_rows:
                    staged = []
                    break
                raise

            staged.append(
                PipelineEvent(
                    source=mapping.source or mapping.modality,
                    modality=mapping.modality,
                    partition_key=str(row.get(partition_key_field, "")),
                    metadata={
                        "row_index": row_index,
                        "feature_fields": list(mapping.feature_fields),
                    },
                    tensor=TensorPayload(
                        shape=[1, len(vector)],
                        values=vector,
                    ),
                )
            )

        if row_failed and drop_invalid_rows:
            dropped_rows += 1
            continue
        events.extend(staged)

    return events, dropped_rows


def _read_connector_bytes(connector: ConnectorConfig) -> bytes:
    if connector.kind == "s3_parquet":
        return _read_s3_bytes(connector)

    if connector.kind.startswith("local_"):
        path = Path(connector.source).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.read_bytes()

    headers = {}
    for header_name, env_name in connector.headers_env.items():
        value = os.getenv(env_name, "")
        if not value:
            raise ValueError(f"Environment variable '{env_name}' is missing for {header_name}")
        headers[header_name] = value
    request = Request(connector.source, headers=headers)
    with urlopen(request, timeout=connector.timeout_seconds) as response:  # nosec B310
        return response.read()


def _parse_rows(connector: ConnectorConfig, raw_bytes: bytes) -> list[dict[str, Any]]:
    if connector.kind in {"local_jsonl", "http_ndjson"}:
        rows = []
        for line in raw_bytes.decode("utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            item = json.loads(stripped)
            if not isinstance(item, dict):
                raise ValueError("NDJSON connectors require object rows")
            rows.append(item)
        return rows

    if connector.kind == "local_csv":
        decoded = raw_bytes.decode("utf-8").splitlines()
        reader = csv.DictReader(decoded)
        return [dict(row) for row in reader]

    if connector.kind in {"local_parquet", "s3_parquet"}:
        table = pq.read_table(pa.BufferReader(raw_bytes))
        return [dict(item) for item in table.to_pylist()]

    if connector.kind == "http_json":
        payload = json.loads(raw_bytes.decode("utf-8"))
        rows = _extract_records(payload, connector.records_path)
        if not all(isinstance(item, dict) for item in rows):
            raise ValueError("JSON connector requires a list of object rows")
        return [dict(item) for item in rows]

    raise ValueError(f"Unsupported connector kind: {connector.kind}")


def _extract_records(payload: Any, records_path: str) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise ValueError("Connector payload must be a list or an object containing a list")

    current: Any = payload
    path = records_path.strip()
    if path:
        for segment in path.split("."):
            if not isinstance(current, dict) or segment not in current:
                raise ValueError(f"records_path '{records_path}' could not be resolved")
            current = current[segment]
        if not isinstance(current, list):
            raise ValueError(f"records_path '{records_path}' did not resolve to a list")
        return current

    for fallback_key in ("records", "items", "data", "results"):
        candidate = payload.get(fallback_key)
        if isinstance(candidate, list):
            return candidate

    raise ValueError("JSON payload did not expose a record list; provide records_path")


def _read_s3_bytes(connector: ConnectorConfig) -> bytes:
    if boto3 is None:
        raise ValueError("boto3 is required for s3_parquet connectors")

    parsed = urlparse(connector.source)
    if parsed.scheme != "s3" or not parsed.netloc or not parsed.path.lstrip("/"):
        raise ValueError("s3_parquet connectors require a source like s3://bucket/key.parquet")

    client_kwargs: dict[str, Any] = {}
    if connector.region:
        client_kwargs["region_name"] = connector.region
    if connector.endpoint_url:
        client_kwargs["endpoint_url"] = connector.endpoint_url

    for argument_name, env_name in connector.secret_env.items():
        value = os.getenv(env_name, "")
        if not value:
            raise ValueError(
                "Environment variable "
                f"'{env_name}' is missing for connector secret '{argument_name}'"
            )
        client_kwargs[argument_name] = value

    client = boto3.client("s3", **client_kwargs)
    response = client.get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))
    body = response.get("Body")
    if body is None or not hasattr(body, "read"):
        raise ValueError("S3 connector did not return a readable object body")
    payload = body.read()
    if isinstance(payload, bytearray):
        return bytes(payload)
    if isinstance(payload, memoryview):
        return payload.tobytes()
    if isinstance(payload, BytesIO):
        return payload.getvalue()
    if not isinstance(payload, bytes):
        raise ValueError("S3 connector body did not resolve to bytes")
    return payload


def _infer_dtype(values: list[Any]) -> str:
    present = [value for value in values if not _is_missing(value)]
    if not present:
        return "string"
    if all(_is_bool_like(value) for value in present):
        return "boolean"
    if all(_is_int_like(value) for value in present):
        return "integer"
    if all(_is_float_like(value) for value in present):
        return "float"
    if all(_is_date_like(value) for value in present):
        return "timestamp"
    return "string"


def _semantic_role(name: str) -> str:
    lowered = name.strip().lower()
    if lowered.endswith("_id") or lowered == "id":
        return "identifier"
    if "date" in lowered or "time" in lowered:
        return "timestamp"
    if "country" in lowered or "region" in lowered or "locale" in lowered:
        return "geography"
    if lowered.startswith("is_") or lowered.startswith("has_"):
        return "flag"
    return ""


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _is_bool_like(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"true", "false", "yes", "no", "0", "1"}
    return False


def _is_int_like(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        try:
            int(value.strip())
            return True
        except ValueError:
            return False
    return False


def _is_float_like(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value.strip())
            return True
        except ValueError:
            return False
    return False


def _is_date_like(value: Any) -> bool:
    if isinstance(value, (date, datetime)):
        return True
    if not isinstance(value, str):
        return False
    candidate = value.strip().replace("Z", "+00:00")
    try:
        datetime.fromisoformat(candidate)
        return True
    except ValueError:
        return False


def _coerce_float(value: Any) -> float:
    if _is_missing(value):
        raise ValueError("Missing numeric feature")
    return float(value)
