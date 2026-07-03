from __future__ import annotations

from .contracts import BenchmarkResult
from .service import AdvancedMultimodalService


def run_smoke_benchmark(
    service: AdvancedMultimodalService | None = None,
    model_id: str = "adaptive_transformer",
    iterations: int = 10,
) -> BenchmarkResult:
    runtime = service or AdvancedMultimodalService()
    return runtime.run_smoke_benchmark(model_id=model_id, iterations=iterations)
