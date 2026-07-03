from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

INFERENCE_REQUESTS = Counter(
    "amai_inference_requests_total",
    "Total multimodal inference requests",
    ["runtime_mode", "model_id"],
)

RETRIEVAL_REQUESTS = Counter(
    "amai_retrieval_requests_total",
    "Total retrieval requests",
    ["backend"],
)

DATA_PLANE_REQUESTS = Counter(
    "amai_data_plane_requests_total",
    "Total non-inference multimodal data plane requests",
    ["surface"],
)

INFERENCE_LATENCY = Histogram(
    "amai_inference_latency_seconds",
    "Inference latency by runtime mode and model",
    ["runtime_mode", "model_id"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
)


@contextmanager
def observe_inference(runtime_mode: str, model_id: str):
    INFERENCE_REQUESTS.labels(runtime_mode=runtime_mode, model_id=model_id).inc()
    started = perf_counter()
    try:
        yield
    finally:
        elapsed = perf_counter() - started
        INFERENCE_LATENCY.labels(runtime_mode=runtime_mode, model_id=model_id).observe(elapsed)


def record_retrieval(backend: str) -> None:
    RETRIEVAL_REQUESTS.labels(backend=backend).inc()


def record_data_plane(surface: str) -> None:
    DATA_PLANE_REQUESTS.labels(surface=surface).inc()


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
