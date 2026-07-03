from __future__ import annotations

from typing import List

from .contracts import (
    InferenceRequest,
    OrchestrationPlan,
    PlanStep,
    VideoCleaningRequest,
    VideoPacketRequest,
)


def build_inference_plan(request: InferenceRequest) -> OrchestrationPlan:
    steps: List[PlanStep] = [
        PlanStep(
            order=1,
            name="validate_payloads",
            detail="Check tensor shapes, modality count, and batch alignment.",
        ),
    ]
    order = 2
    if request.target == "retrieval" or request.metadata.get("attach_context"):
        steps.append(
            PlanStep(
                order=order,
                name="retrieve_context",
                detail=(
                    "Search the vector lane for nearby multimodal context "
                    "before inference."
                ),
            )
        )
        order += 1

    for modality in sorted(request.modalities.keys()):
        detail = f"Project {modality} into the shared runtime lane."
        if modality == "video":
            detail = "Reduce the video stream into temporal evidence windows before shared fusion."
        steps.append(PlanStep(order=order, name=f"encode_{modality}", detail=detail))
        order += 1

    steps.extend(
        [
            PlanStep(
                order=order,
                name="fuse_modalities",
                detail="Compose modality signatures into one fused representation.",
            ),
            PlanStep(
                order=order + 1,
                name="emit_target",
                detail=(
                    f"Return the {request.target} surface with summaries "
                    "and runtime warnings kept explicit."
                ),
            ),
        ]
    )

    return OrchestrationPlan(
        request_id=request.metadata.get("request_id", request.model_id),
        model_id=request.model_id,
        runtime_mode=request.runtime_mode,
        target=request.target,
        source_modalities=sorted(request.modalities.keys()),
        steps=steps,
    )


def build_video_packet_steps(request: VideoPacketRequest | VideoCleaningRequest) -> List[PlanStep]:
    steps = [
        PlanStep(
            order=1,
            name="read_transcript",
            detail="Use transcript timing as the primary reading surface.",
        ),
        PlanStep(
            order=2,
            name="scan_signals",
            detail="Fold frame motion, focus, and audio energy into the clip map.",
        ),
        PlanStep(
            order=3,
            name="mark_boundaries",
            detail="Surface silence gaps, filler spans, and unstable transitions.",
        ),
    ]
    if isinstance(request, VideoCleaningRequest):
        steps.append(
            PlanStep(
                order=4,
                name="assemble_cut_script",
                detail="Emit kept spans and removed spans as a deterministic cleanup plan.",
            )
        )
    else:
        steps.append(
            PlanStep(
                order=4,
                name="assemble_evidence",
                detail=(
                    "Return evidence windows the retrieval or editing lane "
                    "can inspect without raw frame dumps."
                ),
            )
        )
    return steps
