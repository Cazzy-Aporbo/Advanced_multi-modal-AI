from __future__ import annotations

from .contracts import BenchmarkResult, ReferenceBenchmarkRequest, ReferenceBenchmarkResult
from .service import AdvancedMultimodalService


def run_smoke_benchmark(
    service: AdvancedMultimodalService | None = None,
    model_id: str = "adaptive_transformer",
    iterations: int = 10,
) -> BenchmarkResult:
    runtime = service or AdvancedMultimodalService()
    return runtime.run_smoke_benchmark(model_id=model_id, iterations=iterations)


def run_reference_benchmark(
    service: AdvancedMultimodalService | None = None,
    *,
    route_count: int,
    request: ReferenceBenchmarkRequest | None = None,
) -> ReferenceBenchmarkResult:
    runtime = service or AdvancedMultimodalService()
    return runtime.run_reference_benchmark(route_count=route_count, request=request)
