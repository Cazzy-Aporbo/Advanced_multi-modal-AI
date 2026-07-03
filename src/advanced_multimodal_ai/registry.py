from __future__ import annotations

from typing import List

from .contracts import RegisteredModelResponse
from .legacy import RESEARCH_MODELS


def list_registered_models(torch_available: bool) -> List[RegisteredModelResponse]:
    models: List[RegisteredModelResponse] = []
    for descriptor in RESEARCH_MODELS.values():
        models.append(
            RegisteredModelResponse(
                model_id=descriptor.model_id,
                label=descriptor.label,
                runtime_ready=descriptor.supports_research_mode and torch_available,
                supports_contract_mode=True,
                supports_research_mode=descriptor.supports_research_mode,
                source_file=descriptor.source_file,
                notes=descriptor.notes,
            )
        )
    return models
