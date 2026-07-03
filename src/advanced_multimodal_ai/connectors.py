from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

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
    WebFetchReceipt,
    WebIngestPolicy,
)


@dataclass(slots=True)
class ConnectorSourcePayload:
    body: bytes
    final_url: str
    status_code: int
    content_type: str
    metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class ConnectorMaterialization:
    rows: list[dict[str, Any]]
    benchmark: ConnectorBenchmark
    web_receipt: WebFetchReceipt | None = None


def materialize_connector_rows(
    connector: ConnectorConfig,
    limit: int,
    prior_web_receipt: WebFetchReceipt | None = None,
) -> ConnectorMaterialization:
    fetch_started = perf_counter()
    payload = _read_connector_payload(
        connector=connector,
        prior_web_receipt=prior_web_receipt,
    )
    fetch_elapsed = (perf_counter() - fetch_started) * 1000

    parse_started = perf_counter()
    rows, web_receipt = _parse_rows(connector=connector, payload=payload)
    trimmed = rows[:limit]
    if web_receipt is not None:
        web_receipt = web_receipt.model_copy(update={"extracted_record_count": len(trimmed)})
    parse_elapsed = (perf_counter() - parse_started) * 1000
    total_elapsed = fetch_elapsed + parse_elapsed

    benchmark = ConnectorBenchmark(
        fetch_ms=float(fetch_elapsed),
        parse_ms=float(parse_elapsed),
        total_ms=float(total_elapsed),
        record_count=len(trimmed),
        bytes_read=len(payload.body),
        rows_per_second=float((len(trimmed) / total_elapsed) * 1000) if total_elapsed else 0.0,
    )
    return ConnectorMaterialization(rows=trimmed, benchmark=benchmark, web_receipt=web_receipt)


def connector_source_domain(source: str) -> str:
    parsed = urlparse(source)
    domain = parsed.netloc.strip().lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


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


def _read_connector_payload(
    connector: ConnectorConfig,
    prior_web_receipt: WebFetchReceipt | None,
) -> ConnectorSourcePayload:
    if connector.kind == "s3_parquet":
        body = _read_s3_bytes(connector)
        return ConnectorSourcePayload(
            body=body,
            final_url=connector.source,
            status_code=200,
            content_type="application/octet-stream",
        )

    if connector.kind.startswith("local_"):
        path = Path(connector.source).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return ConnectorSourcePayload(
            body=path.read_bytes(),
            final_url=str(path),
            status_code=200,
            content_type=_local_content_type(connector.kind),
        )

    if connector.kind == "web_html":
        return _read_web_html_payload(connector, prior_web_receipt)

    headers = _resolve_headers(connector)
    request = Request(connector.source, headers=headers)
    with urlopen(request, timeout=connector.timeout_seconds) as response:  # nosec B310
        return ConnectorSourcePayload(
            body=response.read(),
            final_url=response.geturl(),
            status_code=int(response.getcode() or 200),
            content_type=response.headers.get("Content-Type", ""),
        )


def _parse_rows(
    connector: ConnectorConfig,
    payload: ConnectorSourcePayload,
) -> tuple[list[dict[str, Any]], WebFetchReceipt | None]:
    if connector.kind in {"local_jsonl", "http_ndjson"}:
        rows = []
        for line in payload.body.decode("utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            item = json.loads(stripped)
            if not isinstance(item, dict):
                raise ValueError("NDJSON connectors require object rows")
            rows.append(item)
        return rows, None

    if connector.kind == "local_csv":
        decoded = payload.body.decode("utf-8").splitlines()
        reader = csv.DictReader(decoded)
        return [dict(row) for row in reader], None

    if connector.kind in {"local_parquet", "s3_parquet"}:
        table = pq.read_table(pa.BufferReader(payload.body))
        return [dict(item) for item in table.to_pylist()], None

    if connector.kind == "http_json":
        body = json.loads(payload.body.decode("utf-8"))
        rows = _extract_records(body, connector.records_path)
        if not all(isinstance(item, dict) for item in rows):
            raise ValueError("JSON connector requires a list of object rows")
        return [dict(item) for item in rows], None

    if connector.kind == "web_html":
        rows, receipt = _extract_rows_from_html(connector, payload)
        return rows, receipt

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


def _read_web_html_payload(
    connector: ConnectorConfig,
    prior_web_receipt: WebFetchReceipt | None,
) -> ConnectorSourcePayload:
    policy = connector.web_policy or WebIngestPolicy()
    domain = connector_source_domain(connector.source)
    if not domain:
        raise ValueError("web_html connectors require a resolvable domain.")

    _ensure_allowed_domain(domain=domain, policy=policy)
    _enforce_request_interval(
        domain=domain,
        policy=policy,
        prior_web_receipt=prior_web_receipt,
    )

    robot_metadata = _inspect_robots_policy(
        source=connector.source,
        policy=policy,
        timeout_seconds=connector.timeout_seconds,
    )
    if policy.respect_robots and not bool(robot_metadata["robots_allowed"]):
        raise ValueError(f"robots policy denied access to {connector.source}")

    headers = {"User-Agent": policy.user_agent}
    payload = _read_http_payload(
        source=connector.source,
        headers=headers,
        timeout_seconds=connector.timeout_seconds,
        max_bytes=policy.max_bytes,
    )
    if "text/html" not in payload.content_type.lower():
        raise ValueError(
            "web_html connectors only accept HTML pages. "
            f"Received content type '{payload.content_type or 'unknown'}'."
        )
    return ConnectorSourcePayload(
        body=payload.body,
        final_url=payload.final_url,
        status_code=payload.status_code,
        content_type=payload.content_type,
        metadata=robot_metadata,
    )


def _ensure_allowed_domain(domain: str, policy: WebIngestPolicy) -> None:
    if not policy.allowed_domains:
        return
    for allowed in policy.allowed_domains:
        if domain == allowed or domain.endswith(f".{allowed}"):
            return
    raise ValueError(
        f"Domain '{domain}' is outside the connector allowlist: {', '.join(policy.allowed_domains)}"
    )


def _enforce_request_interval(
    domain: str,
    policy: WebIngestPolicy,
    prior_web_receipt: WebFetchReceipt | None,
) -> None:
    if policy.min_interval_ms <= 0 or prior_web_receipt is None:
        return
    if connector_source_domain(prior_web_receipt.final_url) != domain:
        return

    previous = _parse_timestamp(prior_web_receipt.created_at)
    elapsed_ms = (datetime.now(timezone.utc) - previous).total_seconds() * 1000
    if elapsed_ms < policy.min_interval_ms:
        remaining_ms = int(policy.min_interval_ms - elapsed_ms)
        raise ValueError(
            f"Domain '{domain}' is still inside the minimum interval. "
            f"Wait at least {remaining_ms} ms before the next fetch."
        )


def _inspect_robots_policy(
    source: str,
    policy: WebIngestPolicy,
    timeout_seconds: float,
) -> dict[str, Any]:
    robots_url = _robots_url(source)
    request = Request(robots_url, headers={"User-Agent": policy.user_agent})
    parser = RobotFileParser()

    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
            lines = response.read().decode("utf-8", errors="ignore").splitlines()
    except HTTPError as error:
        if error.code in {404, 410}:
            return {
                "robots_url": robots_url,
                "robots_allowed": True,
                "crawl_delay_seconds": None,
                "request_rate": "",
                "sitemap_urls": [],
            }
        raise ValueError(
            f"Could not confirm robots policy for {source}; robots.txt returned {error.code}."
        ) from error
    except URLError as error:
        raise ValueError(f"Could not reach robots policy for {source}: {error.reason}") from error

    parser.parse(lines)
    rate = parser.request_rate(policy.user_agent)
    rate_text = ""
    if rate is not None:
        rate_text = f"{rate.requests}/{rate.seconds}s"
    return {
        "robots_url": robots_url,
        "robots_allowed": parser.can_fetch(policy.user_agent, source),
        "crawl_delay_seconds": parser.crawl_delay(policy.user_agent),
        "request_rate": rate_text,
        "sitemap_urls": parser.site_maps() or [],
    }


def _extract_rows_from_html(
    connector: ConnectorConfig,
    payload: ConnectorSourcePayload,
) -> tuple[list[dict[str, Any]], WebFetchReceipt]:
    policy = connector.web_policy or WebIngestPolicy()
    metadata = payload.metadata or {}

    extractor = _HtmlRecordExtractor()
    extractor.feed(payload.body.decode("utf-8", errors="ignore"))
    extractor.close()

    title = extractor.title.strip()
    rows = _rows_from_html_blocks(
        blocks=extractor.blocks,
        title=title,
        final_url=payload.final_url,
        extract_mode=policy.extract_mode,
        include_title=policy.include_title,
        include_headings=policy.include_headings,
    )
    if not rows:
        raise ValueError("web_html connectors did not yield any readable content blocks.")

    receipt = WebFetchReceipt(
        url=connector.source,
        final_url=payload.final_url,
        domain=connector_source_domain(payload.final_url),
        status_code=payload.status_code,
        content_type=payload.content_type,
        robots_url=str(metadata.get("robots_url", "")),
        robots_allowed=bool(metadata.get("robots_allowed", True)),
        crawl_delay_seconds=metadata.get("crawl_delay_seconds"),
        request_rate=str(metadata.get("request_rate", "")),
        sitemap_urls=list(metadata.get("sitemap_urls", [])),
        bytes_read=len(payload.body),
        extracted_record_count=len(rows),
        policy_user_agent=policy.user_agent,
        title=title,
        notes=_build_web_receipt_notes(policy=policy, rows=rows),
    )
    return rows, receipt


def _read_http_payload(
    source: str,
    headers: dict[str, str],
    timeout_seconds: float,
    max_bytes: int,
) -> ConnectorSourcePayload:
    request = Request(source, headers=headers)
    with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise ValueError(
                f"HTTP payload exceeded the configured byte limit of {max_bytes} bytes."
            )
        return ConnectorSourcePayload(
            body=body,
            final_url=response.geturl(),
            status_code=int(response.getcode() or 200),
            content_type=response.headers.get("Content-Type", ""),
        )


def _resolve_headers(connector: ConnectorConfig) -> dict[str, str]:
    headers: dict[str, str] = {}
    for header_name, env_name in connector.headers_env.items():
        value = os.getenv(env_name, "")
        if not value:
            raise ValueError(f"Environment variable '{env_name}' is missing for {header_name}")
        headers[header_name] = value
    return headers


def _robots_url(source: str) -> str:
    parsed = urlparse(source)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def _rows_from_html_blocks(
    *,
    blocks: list[dict[str, Any]],
    title: str,
    final_url: str,
    extract_mode: str,
    include_title: bool,
    include_headings: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    domain = connector_source_domain(final_url)
    position_index = 0

    def append_row(block_kind: str, text: str, heading_level: int = 0, link_count: int = 0) -> None:
        nonlocal position_index
        cleaned = " ".join(text.split())
        if not cleaned:
            return
        rows.append(
            {
                "record_id": f"{domain}-{position_index:04d}",
                "source_url": final_url,
                "domain": domain,
                "page_title": title,
                "block_kind": block_kind,
                "heading_level": heading_level,
                "position_index": position_index,
                "text": cleaned,
                "char_count": len(cleaned),
                "word_count": len(cleaned.split()),
                "sentence_count": max(1, sum(cleaned.count(marker) for marker in ".!?")),
                "link_count": link_count,
            }
        )
        position_index += 1

    if include_title and title:
        append_row("title", title)

    for block in blocks:
        kind = str(block["kind"])
        if kind == "heading" and not include_headings:
            continue
        if extract_mode == "paragraphs" and kind not in {"paragraph", "list_item"}:
            continue
        if extract_mode == "headings" and kind != "heading":
            continue
        append_row(
            block_kind=kind,
            text=str(block["text"]),
            heading_level=int(block.get("heading_level", 0) or 0),
            link_count=int(block.get("link_count", 0) or 0),
        )

    return rows


def _build_web_receipt_notes(
    *,
    policy: WebIngestPolicy,
    rows: list[dict[str, Any]],
) -> list[str]:
    notes = [
        f"extract mode: {policy.extract_mode}",
        f"blocks kept: {len(rows)}",
    ]
    if policy.allowed_domains:
        notes.append(f"allowlist: {', '.join(policy.allowed_domains)}")
    if policy.min_interval_ms:
        notes.append(f"minimum interval: {policy.min_interval_ms} ms")
    return notes


def _local_content_type(kind: str) -> str:
    mapping = {
        "local_csv": "text/csv",
        "local_jsonl": "application/x-ndjson",
        "local_parquet": "application/octet-stream",
    }
    return mapping.get(kind, "application/octet-stream")


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
    if lowered in {
        "char_count",
        "word_count",
        "sentence_count",
        "heading_level",
        "link_count",
        "position_index",
    }:
        return "measurement"
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


def _parse_timestamp(value: str) -> datetime:
    candidate = value.replace("Z", "+00:00")
    return datetime.fromisoformat(candidate)


class _HtmlRecordExtractor(HTMLParser):
    _heading_tags = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
    _block_tags = {"p": "paragraph", "li": "list_item"}
    _skip_tags = {"script", "style", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.blocks: list[dict[str, Any]] = []
        self._active_tag: str | None = None
        self._active_parts: list[str] = []
        self._active_link_count = 0
        self._skip_depth = 0
        self._title_open = False

    @property
    def title(self) -> str:
        return " ".join(part for part in self.title_parts if part).strip()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in self._skip_tags:
            self._skip_depth += 1
            return
        if lowered == "title":
            self._title_open = True
            return
        if self._skip_depth:
            return
        if lowered in self._heading_tags or lowered in self._block_tags:
            self._active_tag = lowered
            self._active_parts = []
            self._active_link_count = 0
            return
        if lowered == "a" and self._active_tag is not None:
            self._active_link_count += 1

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in self._skip_tags:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if lowered == "title":
            self._title_open = False
            return
        if self._skip_depth or self._active_tag != lowered:
            return

        text = " ".join(part for part in self._active_parts if part).strip()
        if text:
            if lowered in self._heading_tags:
                self.blocks.append(
                    {
                        "kind": "heading",
                        "text": text,
                        "heading_level": self._heading_tags[lowered],
                        "link_count": self._active_link_count,
                    }
                )
            else:
                self.blocks.append(
                    {
                        "kind": self._block_tags[lowered],
                        "text": text,
                        "heading_level": 0,
                        "link_count": self._active_link_count,
                    }
                )
        self._active_tag = None
        self._active_parts = []
        self._active_link_count = 0

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        if self._title_open:
            self.title_parts.append(text)
        if self._skip_depth or self._active_tag is None:
            return
        self._active_parts.append(text)
