from __future__ import annotations

from fastapi.testclient import TestClient

import advanced_multimodal_ai.connectors as connector_module
from advanced_multimodal_ai.api import create_app

client = TestClient(create_app())


class _FakeResponse:
    def __init__(
        self,
        body: bytes,
        url: str,
        status_code: int,
        content_type: str,
    ) -> None:
        self._body = body
        self._url = url
        self._status_code = status_code
        self.headers = {"Content-Type": content_type}

    def read(self, amount: int | None = None) -> bytes:
        if amount is None:
            return self._body
        return self._body[:amount]

    def geturl(self) -> str:
        return self._url

    def getcode(self) -> int:
        return self._status_code

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def _install_public_page_stub(monkeypatch, *, title: str = "Quiet Signals") -> None:
    html = f"""
    <html>
      <head><title>{title}</title></head>
      <body>
        <h1>{title}</h1>
        <p>Pattern shifts deserve patient reading.</p>
        <p>Each page can become a measured row rather than a loose note.</p>
      </body>
    </html>
    """.encode("utf-8")
    robots = b"User-agent: *\nAllow: /\nCrawl-delay: 2\nSitemap: https://example.com/sitemap.xml\n"

    def fake_urlopen(request, timeout=0):  # noqa: ARG001
        url = request.full_url
        if url.endswith("/robots.txt"):
            return _FakeResponse(robots, url, 200, "text/plain; charset=utf-8")
        return _FakeResponse(html, url, 200, "text/html; charset=utf-8")

    monkeypatch.setattr(connector_module, "urlopen", fake_urlopen)


def test_web_html_connector_registers_rows_and_persists_receipt(monkeypatch):
    _install_public_page_stub(monkeypatch)

    response = client.post(
        "/v1/connectors/register",
        json={
            "connector": {
                "kind": "web_html",
                "source": "https://example.com/research/quiet-signals",
                "web_policy": {
                    "allowed_domains": ["example.com"],
                    "min_interval_ms": 0,
                    "extract_mode": "article_blocks",
                },
            },
            "dataset_name": "public_page_rows",
            "owner": "cazandra",
            "version": "2026.07.02",
            "partition_keys": ["source_url"],
            "primary_keys": ["record_id"],
            "tags": ["public-web", "ethics"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["record_count"] >= 3
    assert any(field["name"] == "word_count" for field in payload["dataset"]["fields"])
    assert any(row["block_kind"] == "title" for row in payload["sample_rows"])

    runs = client.get("/v1/connectors/runs").json()
    matching = [item for item in runs if item["dataset_name"] == "public_page_rows"]
    assert matching
    latest = matching[0]
    assert latest["connector_kind"] == "web_html"
    assert latest["web_receipt"]["robots_allowed"] is True
    assert latest["web_receipt"]["title"] == "Quiet Signals"
    assert latest["web_receipt"]["sitemap_urls"] == ["https://example.com/sitemap.xml"]


def test_web_html_connector_pipeline_ingest_maps_numeric_features(monkeypatch):
    _install_public_page_stub(monkeypatch, title="Measured Pages")

    response = client.post(
        "/v1/connectors/pipeline-ingest",
        json={
            "connector": {
                "kind": "web_html",
                "source": "https://example.com/research/measured-pages",
                "web_policy": {
                    "allowed_domains": ["example.com"],
                    "min_interval_ms": 0,
                    "extract_mode": "article_blocks",
                },
            },
            "dataset_name": "measured_page_rows",
            "owner": "cazandra",
            "version": "2026.07.02",
            "stream_id": "public-page-stream",
            "batch_label": "page-window-01",
            "partition_key_field": "source_url",
            "modality_mappings": [
                {
                    "modality": "tabular",
                    "feature_fields": ["word_count", "char_count", "sentence_count"],
                    "source": "text-shape",
                },
                {
                    "modality": "sensor",
                    "feature_fields": ["heading_level", "link_count", "position_index"],
                    "source": "layout-shape",
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["connector_run"]["connector_kind"] == "web_html"
    assert payload["connector_run"]["web_receipt"]["title"] == "Measured Pages"
    assert payload["pipeline_run"]["status"] == "accepted"
    assert payload["pipeline_run"]["modality_counts"]["tabular"] >= 1
    assert payload["pipeline_run"]["modality_counts"]["sensor"] >= 1


def test_web_html_connector_enforces_minimum_interval(monkeypatch):
    _install_public_page_stub(monkeypatch, title="Interval Lane")

    request = {
        "connector": {
            "kind": "web_html",
            "source": "https://interval.example.org/research/interval-lane",
            "web_policy": {
                "allowed_domains": ["example.org"],
                "min_interval_ms": 60000,
                "extract_mode": "article_blocks",
            },
        },
        "dataset_name": "interval_page_rows",
        "owner": "cazandra",
        "version": "2026.07.02",
        "partition_keys": ["source_url"],
        "primary_keys": ["record_id"],
    }

    first = client.post("/v1/connectors/register", json=request)
    assert first.status_code == 200

    second = client.post(
        "/v1/connectors/register",
        json={**request, "version": "2026.07.03"},
    )
    assert second.status_code == 400
    assert "minimum interval" in second.json()["detail"].lower()
