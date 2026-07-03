from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import uvicorn

from .api import create_app
from .benchmarks import run_smoke_benchmark


def serve_command() -> None:
    host = os.getenv("AMAI_HOST", "0.0.0.0")
    port = int(os.getenv("AMAI_PORT", "8000"))
    uvicorn.run("advanced_multimodal_ai.api:create_app", factory=True, host=host, port=port)


def benchmark_command(model_id: str = "adaptive_transformer", iterations: int = 10) -> None:
    result = run_smoke_benchmark(model_id=model_id, iterations=iterations)
    print(json.dumps(result.model_dump(), indent=2))


def export_openapi_command(output_path: str = "openapi/openapi.json") -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    schema = create_app().openapi()
    target.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(target)


def recipe_export_command(recipe_id: str, output_path: str) -> None:
    from .service import AdvancedMultimodalService

    service = AdvancedMultimodalService()
    record = service.get_recipe(recipe_id)
    if record is None:
        raise SystemExit(f"recipe not found: {recipe_id}")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(record.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    print(target)


def main() -> None:
    parser = argparse.ArgumentParser(description="Advanced Multi-modal AI command surface.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="run the FastAPI service")
    serve_parser.add_argument("--host", default=os.getenv("AMAI_HOST", "0.0.0.0"))
    serve_parser.add_argument("--port", type=int, default=int(os.getenv("AMAI_PORT", "8000")))

    benchmark_parser = subparsers.add_parser("benchmark", help="run a smoke benchmark")
    benchmark_parser.add_argument("--model-id", default="adaptive_transformer")
    benchmark_parser.add_argument("--iterations", type=int, default=10)

    openapi_parser = subparsers.add_parser("openapi", help="export the OpenAPI schema")
    openapi_parser.add_argument("--output", default="openapi/openapi.json")

    recipe_export_parser = subparsers.add_parser(
        "recipe-export",
        help="export a compiled recipe manifest",
    )
    recipe_export_parser.add_argument("--recipe-id", required=True)
    recipe_export_parser.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.command == "serve":
        uvicorn.run(
            "advanced_multimodal_ai.api:create_app",
            factory=True,
            host=args.host,
            port=args.port,
        )
        return

    if args.command == "benchmark":
        benchmark_command(model_id=args.model_id, iterations=args.iterations)
        return

    if args.command == "openapi":
        export_openapi_command(output_path=args.output)
        return

    if args.command == "recipe-export":
        recipe_export_command(recipe_id=args.recipe_id, output_path=args.output)
        return

    raise ValueError(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
