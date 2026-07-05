from __future__ import annotations

import ast
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings
from .contracts import RepositoryFileEdge, RepositoryFileMap, RepositoryFileNode

REPO_ROOT = Path(__file__).resolve().parents[2]

DISCOVERY_GLOBS = (
    "src/advanced_multimodal_ai/**/*.py",
    "scripts/*.py",
    "tests/*.py",
    "examples/*.py",
    "crates/**/*.rs",
    "*.js",
    "*.html",
    "proof/*.json",
    "proof/*.md",
    "docs/*.md",
    "*.md",
)

SKIP_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".hypothesis",
    ".git",
    "target",
    "node_modules",
    "advanced_multimodal_ai.egg-info",
}

LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".rs": "Rust",
    ".js": "JavaScript",
    ".html": "HTML",
    ".json": "JSON",
    ".md": "Markdown",
    ".toml": "TOML",
    ".yaml": "YAML",
    ".yml": "YAML",
}


def build_repository_file_map(*, settings: Settings) -> RepositoryFileMap:
    paths = _discover_files()
    module_paths = _python_module_paths(paths)
    path_set = {path.as_posix() for path in paths}
    edges = _build_edges(paths, module_paths, path_set)
    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    for edge in edges:
        outgoing[edge.source].append(edge)
        incoming[edge.target].append(edge)

    nodes = [
        _build_node(
            path=path,
            outgoing=outgoing.get(path.as_posix(), []),
            incoming=incoming.get(path.as_posix(), []),
        )
        for path in paths
    ]
    nodes.sort(
        key=lambda node: (
            _lane_sort_key(node.lane),
            -node.complexity_score,
            node.path,
        )
    )

    lane_counts = Counter(node.lane for node in nodes)
    language_counts = Counter(node.language for node in nodes)
    top_connected = sorted(
        nodes,
        key=lambda node: (
            len(node.connects_to) + len(node.imported_by),
            node.complexity_score,
            node.line_count,
        ),
        reverse=True,
    )[:12]

    return RepositoryFileMap(
        service=settings.service_name,
        version=settings.service_version,
        file_count=len(nodes),
        edge_count=len(edges),
        active_python_files=sum(
            1
            for node in nodes
            if node.language == "Python" and node.status in {"active", "supporting"}
        ),
        frontend_files=sum(1 for node in nodes if node.status == "frontend"),
        proof_files=sum(1 for node in nodes if node.status == "proof"),
        lane_counts=dict(sorted(lane_counts.items())),
        language_counts=dict(sorted(language_counts.items())),
        nodes=nodes,
        edges=edges,
        top_connected=top_connected,
    )


def _discover_files() -> list[Path]:
    discovered: dict[str, Path] = {}
    for pattern in DISCOVERY_GLOBS:
        for path in REPO_ROOT.glob(pattern):
            if not path.is_file():
                continue
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            if path.name.endswith((".pyc", ".png", ".jpg", ".jpeg", ".gif", ".zip")):
                continue
            relative = path.relative_to(REPO_ROOT)
            discovered[relative.as_posix()] = relative
    return [discovered[key] for key in sorted(discovered)]


def _python_module_paths(paths: list[Path]) -> dict[str, str]:
    modules: dict[str, str] = {}
    for path in paths:
        if path.suffix != ".py" or not path.as_posix().startswith("src/"):
            continue
        parts = list(path.with_suffix("").parts[1:])
        if parts[-1] == "__init__":
            parts = parts[:-1]
        module_name = ".".join(parts)
        modules[module_name] = path.as_posix()
    return modules


def _build_edges(
    paths: list[Path],
    module_paths: dict[str, str],
    path_set: set[str],
) -> list[RepositoryFileEdge]:
    edges: dict[tuple[str, str, str], RepositoryFileEdge] = {}
    for path in paths:
        source = path.as_posix()
        text = _safe_read(path)
        for target, relation in _extract_file_references(path, text, module_paths, path_set):
            if target == source:
                continue
            key = (source, target, relation)
            edges[key] = RepositoryFileEdge(
                source=source,
                target=target,
                relation=relation,
                weight=_edge_weight(relation),
            )
    return sorted(edges.values(), key=lambda edge: (edge.source, edge.target, edge.relation))


def _extract_file_references(
    path: Path,
    text: str,
    module_paths: dict[str, str],
    path_set: set[str],
) -> list[tuple[str, str]]:
    if path.suffix == ".py":
        return _extract_python_references(path, text, module_paths, path_set)
    if path.suffix in {".html", ".js", ".md"}:
        return _extract_text_references(path, text, path_set)
    if path.as_posix().startswith("proof/"):
        return []
    return _extract_text_references(path, text, path_set)


def _extract_python_references(
    path: Path,
    text: str,
    module_paths: dict[str, str],
    path_set: set[str],
) -> list[tuple[str, str]]:
    references: list[tuple[str, str]] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return references

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = _module_to_path(alias.name, module_paths)
                if target:
                    references.append((target, "imports"))
        elif isinstance(node, ast.ImportFrom):
            module_name = _resolve_from_import(path, node.module or "", node.level, module_paths)
            target = _module_to_path(module_name, module_paths)
            if target:
                references.append((target, "imports"))

    for match in re.finditer(r"['\"]([^'\"]+\.(?:json|md|html|js|py|rs))['\"]", text):
        target = match.group(1).lstrip("./")
        if target in path_set:
            relation = "exports" if "write_text" in text or "openapi" in target else "reads"
            references.append((target, relation))

    if path.as_posix().startswith("tests/"):
        for target in sorted(path_set):
            if target.startswith("src/advanced_multimodal_ai/"):
                module_hint = target.removeprefix("src/").removesuffix(".py").replace("/", ".")
                if module_hint in text:
                    references.append((target, "tests"))

    return references


def _extract_text_references(
    path: Path,
    text: str,
    path_set: set[str],
) -> list[tuple[str, str]]:
    references: list[tuple[str, str]] = []
    current_dir = path.parent
    patterns = (
        r"(?:href|src)=['\"]([^'\"]+)['\"]",
        r"fetch\(['\"]([^'\"]+)['\"]",
        r"`([^`]+\.(?:py|js|html|json|md|rs))`",
        r"\b((?:src|scripts|tests|examples|proof|docs|crates)/[A-Za-z0-9_./-]+\.(?:py|js|html|json|md|rs))",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            raw = match.group(1).split("#", 1)[0].split("?", 1)[0]
            if raw.startswith(("http://", "https://", "mailto:", "#", "/")):
                continue
            root_prefixed = raw.startswith(
                ("src/", "scripts/", "tests/", "examples/", "proof/", "docs/", "crates/")
            )
            candidate = raw if root_prefixed else (current_dir / raw).as_posix()
            candidate = candidate.removeprefix("./")
            if candidate in path_set:
                relation = "renders" if path.suffix in {".html", ".js"} else "documents"
                references.append((candidate, relation))
    return references


def _resolve_from_import(
    path: Path,
    module: str,
    level: int,
    module_paths: dict[str, str],
) -> str:
    if level <= 0:
        return module

    current = path.with_suffix("")
    parts = list(current.parts[1:])
    if parts and parts[-1] != "__init__":
        parts = parts[:-1]
    if level > 1:
        parts = parts[: -(level - 1)]
    if module:
        parts.extend(module.split("."))
    candidate = ".".join(parts)
    if candidate in module_paths:
        return candidate
    while parts:
        candidate = ".".join(parts)
        if candidate in module_paths:
            return candidate
        parts.pop()
    return module


def _module_to_path(module: str, module_paths: dict[str, str]) -> str | None:
    if module in module_paths:
        return module_paths[module]
    parts = module.split(".")
    while parts:
        candidate = ".".join(parts)
        if candidate in module_paths:
            return module_paths[candidate]
        parts.pop()
    return None


def _build_node(
    *,
    path: Path,
    outgoing: list[RepositoryFileEdge],
    incoming: list[RepositoryFileEdge],
) -> RepositoryFileNode:
    text = _safe_read(path)
    relative = path.as_posix()
    absolute = REPO_ROOT / path
    stats = absolute.stat()
    line_count = text.count("\n") + (1 if text else 0)
    route_count = len(re.findall(r"@app\.(?:get|post|put|delete|patch)", text))
    test_count = len(re.findall(r"\bdef test_[A-Za-z0-9_]+", text))
    lane = _lane_for_path(relative, text)
    status = _status_for_path(relative)
    inputs = _infer_inputs(relative, text, outgoing)
    outputs = _infer_outputs(relative, text, incoming)
    evidence = _infer_evidence(relative, text, incoming, outgoing)
    connected_paths = sorted({edge.target for edge in outgoing})[:10]
    imported_by = sorted({edge.source for edge in incoming})[:10]
    complexity = _complexity_score(
        line_count=line_count,
        route_count=route_count,
        test_count=test_count,
        connection_count=len(outgoing) + len(incoming),
        evidence_count=len(evidence),
        status=status,
    )

    return RepositoryFileNode(
        path=relative,
        label=path.name,
        language=LANGUAGE_BY_SUFFIX.get(path.suffix, path.suffix.lstrip(".").upper() or "Text"),
        lane=lane,
        status=status,
        purpose=_purpose_for_file(path, text, lane),
        inputs=inputs,
        outputs=outputs,
        connects_to=connected_paths,
        imported_by=imported_by,
        evidence=evidence,
        line_count=line_count,
        byte_count=stats.st_size,
        route_count=route_count,
        test_count=test_count,
        complexity_score=complexity,
        modified_at=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat(),
    )


def _lane_for_path(path: str, text: str) -> str:
    if path.startswith("tests/"):
        return "verification"
    if path.startswith("scripts/"):
        return "export and proof"
    if path.startswith("proof/"):
        return "generated evidence"
    if path.endswith(".html") or path.endswith(".js") or path.endswith(".css"):
        return "public interface"
    if path.startswith("crates/"):
        return "compiled signal core"
    if "music_" in path:
        return "audio warehouse"
    if "privacy" in path:
        return "privacy membrane"
    if "industrial" in path:
        return "industrial diagnostics"
    if "connector" in path or "pipeline" in path:
        return "data movement"
    if "drift" in path or "bias" in path or "liability" in path:
        return "risk and drift"
    if "repository_" in path or "research_" in path or "operator_" in path:
        return "research surfaces"
    if "@app." in text or path.endswith("service.py") or path.endswith("api.py"):
        return "runtime composition"
    if path.startswith("docs/") or path.endswith(".md"):
        return "documentation"
    return "runtime support"


def _status_for_path(path: str) -> str:
    if path.startswith("tests/"):
        return "test"
    if path.startswith("proof/"):
        return "proof"
    if path.endswith(".html") or path.endswith(".js") or path.endswith(".css"):
        return "frontend"
    if path.startswith("src/") or path.startswith("scripts/") or path.startswith("crates/"):
        return "active"
    return "supporting"


def _purpose_for_file(path: Path, text: str, lane: str) -> str:
    if path.suffix == ".py":
        docstring = _python_docstring(text)
        if docstring:
            return _one_line(docstring)
    if path.suffix == ".html":
        title = _html_title(text)
        if title:
            return f"Renders the {title} public surface."
    if path.suffix == ".js":
        return "Hydrates browser-facing proof data into interactive cards, charts, or controls."
    if path.suffix == ".rs":
        return "Provides compiled signal primitives for deterministic multimodal scoring."
    if path.as_posix().startswith("proof/"):
        return "Stores a generated proof surface read by the public atlas and review workflows."
    if path.suffix == ".md":
        return "Documents repository use, contribution, security, or generated proof context."
    return f"Supports the {lane} lane."


def _infer_inputs(
    path: str,
    text: str,
    outgoing: list[RepositoryFileEdge],
) -> list[str]:
    inputs: list[str] = []
    if "@app.post" in text:
        inputs.append("validated HTTP request bodies")
    if "@app.get" in text:
        inputs.append("route query parameters and persisted runtime state")
    if "BaseModel" in text or "Field(" in text:
        inputs.append("typed contract fields")
    if "TestClient" in text:
        inputs.append("live FastAPI route responses")
    if "pyarrow" in text or "parquet" in text.lower():
        inputs.append("Arrow or Parquet tables")
    if "sqlite" in text.lower():
        inputs.append("local persisted runtime records")
    if "fetch(" in text:
        inputs.append("generated proof JSON or live API payloads")
    if path.startswith("proof/"):
        inputs.append("export script output")
    if outgoing:
        inputs.append(f"{len(outgoing)} referenced file connections")
    return _dedupe(inputs) or ["source code and local repository state"]


def _infer_outputs(
    path: str,
    text: str,
    incoming: list[RepositoryFileEdge],
) -> list[str]:
    outputs: list[str] = []
    if "write_text" in text or path.startswith("proof/"):
        outputs.append("versioned proof artifacts")
    if "return service." in text or "@app." in text:
        outputs.append("typed API responses")
    if "finish_script_execution" in text:
        outputs.append("execution journal receipts")
    if "model_dump" in text or "BaseModel" in text:
        outputs.append("schema-checked payloads")
    if "innerHTML" in text or path.endswith(".html"):
        outputs.append("interactive browser surface")
    if "sqlite" in text.lower():
        outputs.append("queryable runtime store rows")
    if path.endswith(".rs"):
        outputs.append("compiled deterministic metrics")
    if incoming:
        outputs.append(f"read by {len(incoming)} repository files")
    return _dedupe(outputs) or ["repository support surface"]


def _infer_evidence(
    path: str,
    text: str,
    incoming: list[RepositoryFileEdge],
    outgoing: list[RepositoryFileEdge],
) -> list[str]:
    evidence: list[str] = []
    if any(edge.relation == "tests" for edge in incoming) or path.startswith("tests/"):
        evidence.append("test-linked")
    if "finish_script_execution" in text:
        evidence.append("journaled export")
    if path.startswith("proof/"):
        evidence.append("generated artifact")
    if any(edge.target.startswith("proof/") for edge in outgoing):
        evidence.append("writes or reads proof files")
    if "@app." in text:
        evidence.append("FastAPI route surface")
    if "Field(" in text and "BaseModel" in text:
        evidence.append("pydantic contract")
    if path.startswith("crates/"):
        evidence.append("compiled lane")
    return _dedupe(evidence) or ["static repository evidence"]


def _complexity_score(
    *,
    line_count: int,
    route_count: int,
    test_count: int,
    connection_count: int,
    evidence_count: int,
    status: str,
) -> int:
    score = (
        min(38, line_count // 18)
        + route_count * 5
        + test_count * 4
        + connection_count * 3
        + evidence_count * 6
    )
    if status in {"active", "test"}:
        score += 8
    if status == "proof":
        score += 4
    return max(0, min(100, score))


def _edge_weight(relation: str) -> float:
    return {
        "imports": 1.0,
        "renders": 0.82,
        "exports": 0.9,
        "tests": 1.0,
        "reads": 0.7,
        "documents": 0.55,
    }.get(relation, 0.5)


def _python_docstring(text: str) -> str:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ""
    return ast.get_docstring(tree) or ""


def _html_title(text: str) -> str:
    title = re.search(r"<title>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    if title:
        return _one_line(title.group(1))
    heading = re.search(r"<h1[^>]*>(.*?)</h1>", text, flags=re.IGNORECASE | re.DOTALL)
    if heading:
        return _one_line(re.sub(r"<[^>]+>", "", heading.group(1)))
    return ""


def _one_line(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()[:220]


def _safe_read(path: Path) -> str:
    try:
        return (REPO_ROOT / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result[:6]


def _lane_sort_key(lane: str) -> int:
    order = {
        "runtime composition": 0,
        "data movement": 1,
        "audio warehouse": 2,
        "risk and drift": 3,
        "privacy membrane": 4,
        "industrial diagnostics": 5,
        "compiled signal core": 6,
        "verification": 7,
        "export and proof": 8,
        "generated evidence": 9,
        "public interface": 10,
        "research surfaces": 11,
        "documentation": 12,
    }
    return order.get(lane, 99)
