from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / "openapi" / "openapi.json"
TS_OUTPUT = ROOT / "sdk" / "typescript" / "src" / "generated-openapi.ts"
PY_OUTPUT = (
    ROOT
    / "sdk"
    / "python"
    / "src"
    / "advanced_multimodal_ai_client"
    / "generated_openapi.py"
)


def _pascalize(name: str) -> str:
    parts = re.split(r"[^a-zA-Z0-9]+", name)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def _camelize(name: str) -> str:
    pascal = _pascalize(name)
    return pascal[:1].lower() + pascal[1:] if pascal else "unnamed"


def _method_name(operation_id: str, method: str, path: str) -> str:
    base = operation_id or f"{method}_{path}"
    return _camelize(base)


def _path_params(operation: dict) -> list[str]:
    return [
        parameter["name"]
        for parameter in operation.get("parameters", [])
        if parameter.get("in") == "path"
    ]


def _query_params(operation: dict) -> list[str]:
    return [
        parameter["name"]
        for parameter in operation.get("parameters", [])
        if parameter.get("in") == "query"
    ]


def _path_template(path: str) -> str:
    return re.sub(
        r"\{([^}]+)\}",
        lambda match: "${encodeURIComponent(String(" + match.group(1) + "))}",
        path,
    )


def render_typescript(spec: dict) -> str:
    lines = [
        "// Generated from openapi/openapi.json. Do not edit by hand.",
        "",
        "export class GeneratedOpenAPIClient {",
        "  constructor(private readonly baseUrl: string) {}",
        "",
        "  private async request<T>(method: string, path: string, payload?: unknown): Promise<T> {",
        "    const response = await fetch(`${this.baseUrl}${path}`, {",
        "      method,",
        (
            "      headers: payload === undefined"
            " ? undefined"
            " : { \"content-type\": \"application/json\" },"
        ),
        "      body: payload === undefined ? undefined : JSON.stringify(payload),",
        "    });",
        "    if (!response.ok) {",
        "      throw new Error(`Request failed with ${response.status}`);",
        "    }",
        "    return response.json() as Promise<T>;",
        "  }",
        "",
    ]
    for path, methods in spec["paths"].items():
        for method, operation in sorted(methods.items()):
            name = _method_name(operation.get("operationId", ""), method, path)
            summary = operation.get("summary") or operation.get("description") or ""
            path_params = _path_params(operation)
            query_params = _query_params(operation)
            has_body = "requestBody" in operation

            args: list[str] = [f"{param}: string | number" for param in path_params]
            if query_params:
                args.append(
                    "query: Record<string, string | number | boolean | undefined> = {}"
                )
            if has_body:
                args.append("payload: unknown")

            signature = ", ".join(args)
            lines.append(f"  /** {summary.strip()} */" if summary else "  /** API operation */")
            lines.append(f"  async {name}({signature}): Promise<unknown> {{")
            lines.append(f"    let path = `{_path_template(path)}`;")
            if query_params:
                lines.extend(
                    [
                        "    const search = new URLSearchParams();",
                        "    for (const [key, value] of Object.entries(query)) {",
                        "      if (value !== undefined) {",
                        "        search.set(key, String(value));",
                        "      }",
                        "    }",
                        "    const queryString = search.toString();",
                        "    if (queryString) {",
                        "      path += `?${queryString}`;",
                        "    }",
                    ]
                )
            if has_body:
                lines.append(
                    f"    return this.request<unknown>(\"{method.upper()}\", path, payload);"
                )
            else:
                lines.append(f"    return this.request<unknown>(\"{method.upper()}\", path);")
            lines.append("  }")
            lines.append("")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def render_python(spec: dict) -> str:
    lines = [
        '"""Generated from openapi/openapi.json. Do not edit by hand."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "import httpx",
        "",
        "",
        "class GeneratedOpenAPIClient:",
        "    def __init__(self, base_url: str, timeout: float = 30.0) -> None:",
        "        self.base_url = base_url.rstrip('/')",
        "        self.timeout = timeout",
        "",
        "    def _request(",
        "        self,",
        "        method: str,",
        "        path: str,",
        "        payload: Any | None = None,",
        "    ) -> Any:",
        "        response = httpx.request(",
        "            method=method,",
        "            url=f\"{self.base_url}{path}\",",
        "            json=payload,",
        "            timeout=self.timeout,",
        "        )",
        "        response.raise_for_status()",
        "        return response.json()",
        "",
    ]
    for path, methods in spec["paths"].items():
        for method, operation in sorted(methods.items()):
            name = _method_name(operation.get("operationId", ""), method, path)
            summary = operation.get("summary") or operation.get("description") or "API operation"
            path_params = _path_params(operation)
            query_params = _query_params(operation)
            has_body = "requestBody" in operation

            args = [f"{param}: str | int" for param in path_params]
            if query_params:
                args.append("query: dict[str, str | int | float | bool] | None = None")
            if has_body:
                args.append("payload: Any")
            signature = ", ".join(["self", *args])
            lines.append(f"    def {name}({signature}) -> Any:")
            lines.append(f'        """{summary.strip()}"""')
            lines.append(f'        path = f"{path}"')
            if query_params:
                lines.extend(
                    [
                        "        if query:",
                        "            encoded = httpx.QueryParams(query)",
                        "            path = f\"{path}?{encoded}\"",
                    ]
                )
            if has_body:
                lines.append(
                    f'        return self._request("{method.upper()}", path, payload=payload)'
                )
            else:
                lines.append(f'        return self._request("{method.upper()}", path)')
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    spec = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    TS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    TS_OUTPUT.write_text(render_typescript(spec), encoding="utf-8")
    PY_OUTPUT.write_text(render_python(spec), encoding="utf-8")

    print(TS_OUTPUT)
    print(PY_OUTPUT)


if __name__ == "__main__":
    main()
