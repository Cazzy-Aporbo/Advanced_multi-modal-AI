from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

from .config import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUST_BIN = REPO_ROOT / "target" / "debug" / "multimodal-core"


def _looks_enabled(settings: Settings) -> bool:
    return settings.rust_core_mode.lower() in {"auto", "cli", "on"}


def resolve_rust_binary(settings: Settings) -> str | None:
    if not _looks_enabled(settings):
        return None
    if settings.rust_core_binary:
        explicit = Path(settings.rust_core_binary)
        return str(explicit) if explicit.exists() else None
    if DEFAULT_RUST_BIN.exists():
        return str(DEFAULT_RUST_BIN)
    cargo_path = shutil.which("cargo")
    if settings.rust_core_mode.lower() == "auto" and cargo_path:
        manifest_path = REPO_ROOT / "Cargo.toml"
        return (
            f"{cargo_path} run --quiet --manifest-path {manifest_path} "
            "--bin multimodal-core --"
        )
    return None


def _run_bridge(command: str, payload: Dict[str, Any], settings: Settings) -> Dict[str, Any] | None:
    binary = resolve_rust_binary(settings)
    if binary is None:
        return None
    if "cargo run" in binary:
        argv = binary.split() + [command]
    else:
        argv = [binary, command]
    try:
        completed = subprocess.run(
            argv,
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True,
            cwd=REPO_ROOT,
            check=True,
            timeout=max(2.0, settings.request_timeout_seconds),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if not completed.stdout:
        return None
    try:
        return json.loads(completed.stdout.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def signature_from_payload(payload: Dict[str, Any], settings: Settings) -> Dict[str, Any] | None:
    return _run_bridge("signature", payload, settings)


def video_cuts_from_payload(payload: Dict[str, Any], settings: Settings) -> Dict[str, Any] | None:
    return _run_bridge("video-cuts", payload, settings)


def schema_fingerprint_from_payload(
    payload: Dict[str, Any], settings: Settings
) -> Dict[str, Any] | None:
    return _run_bridge("schema-fingerprint", payload, settings)


def tensor_guard_from_payload(
    payload: Dict[str, Any], settings: Settings
) -> Dict[str, Any] | None:
    return _run_bridge("tensor-guard", payload, settings)
