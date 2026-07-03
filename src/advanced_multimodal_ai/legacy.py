from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Callable, Dict, Optional


@dataclass(frozen=True)
class LegacyModelDescriptor:
    model_id: str
    label: str
    source_file: str
    supports_research_mode: bool
    notes: str
    loader: Optional[Callable[[], object]] = None


def _load_adaptive_factory():
    module = import_module("dynamic_transformer")
    return module.create_advanced_multimodal_model


def _load_complete_factory():
    module = import_module("complete_model")
    return module.create_model


RESEARCH_MODELS: Dict[str, LegacyModelDescriptor] = {
    "adaptive_transformer": LegacyModelDescriptor(
        model_id="adaptive_transformer",
        label="Adaptive Multimodal Transformer",
        source_file="dynamic_transformer.py",
        supports_research_mode=True,
        notes=(
            "Factory-backed multimodal transformer with hierarchical fusion "
            "and optional uncertainty output."
        ),
        loader=_load_adaptive_factory,
    ),
    "complete_multimodal": LegacyModelDescriptor(
        model_id="complete_multimodal",
        label="Complete Multimodal AI",
        source_file="complete_model.py",
        supports_research_mode=True,
        notes=(
            "Integrated research model covering modality-specific encoders, "
            "routing, memory augmentation, and training helpers."
        ),
        loader=_load_complete_factory,
    ),
    "fusion_lab": LegacyModelDescriptor(
        model_id="fusion_lab",
        label="Fusion Strategy Lab",
        source_file="fusion_strategies.py",
        supports_research_mode=False,
        notes=(
            "Reusable fusion modules for concatenation, gated fusion, "
            "bilinear pooling, and hierarchical mixing."
        ),
    ),
    "attention_core": LegacyModelDescriptor(
        model_id="attention_core",
        label="Attention Core",
        source_file="core/attention_mechanisms.py",
        supports_research_mode=False,
        notes=(
            "Cross-modal attention primitives and sparse attention "
            "experiments used by the larger research models."
        ),
    ),
}
