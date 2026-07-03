from __future__ import annotations

from .catalog_store import CatalogStore
from .contracts import (
    DatasetRecord,
    RecipeCompileRequest,
    RecipeDatasetResolution,
    RecipeLaunchCommand,
    RecipeLaunchProfile,
    RecipeRecord,
    RecipeSourceSpec,
)


def compile_recipe_record(
    request: RecipeCompileRequest,
    *,
    catalog_store: CatalogStore,
) -> RecipeRecord:
    draft = RecipeRecord(
        label=request.label,
        owner=request.owner,
        objective=request.objective,
        model=request.model,
        sources=request.sources,
        training=request.training,
        distributed=request.distributed,
        evaluation=request.evaluation,
        tags=request.tags,
        notes=request.notes,
    )

    resolved_sources = [
        _resolve_source(
            source=source,
            catalog_store=catalog_store,
        )
        for source in request.sources
    ]

    verified_manifest_path = f".runtime/recipes/{draft.recipe_id}/recipe.json"
    verified_commands = [
        RecipeLaunchCommand(
            label="export_manifest",
            command=(
                "python3 -m advanced_multimodal_ai.cli "
                f"recipe-export --recipe-id {draft.recipe_id} --output {verified_manifest_path}"
            ),
            verified=True,
        ),
        RecipeLaunchCommand(
            label="validate_manifest",
            command=f"python3 scripts/validate_recipe_manifest.py {verified_manifest_path}",
            verified=True,
        ),
        RecipeLaunchCommand(
            label="runtime_acceptance",
            command="python3 scripts/run_acceptance_spine.py",
            verified=True,
        ),
    ]

    worker_count = request.distributed.node_count * request.distributed.devices_per_node
    estimated_global_batch = (
        request.training.micro_batch_size
        * request.training.gradient_accumulation_steps
        * worker_count
    )
    launcher = "torchrun" if worker_count > 1 or request.distributed.engine != "local" else "python"
    launch_profile = RecipeLaunchProfile(
        launcher=launcher,
        engine=request.distributed.engine,
        node_count=request.distributed.node_count,
        devices_per_node=request.distributed.devices_per_node,
        estimated_global_batch_size=estimated_global_batch,
        verified_commands=verified_commands,
        launcher_template=_launcher_template(
            request=request,
            manifest_path=verified_manifest_path,
        ),
        artifacts=[
            verified_manifest_path,
            f".runtime/recipes/{draft.recipe_id}/execution-notes.md",
        ],
        environment=request.distributed.launcher_env,
        notes=_launch_notes(request, resolved_sources),
    )

    warnings = _compile_warnings(request, resolved_sources)
    proof_obligations = _proof_obligations(request, resolved_sources)

    return draft.model_copy(
        update={
            "resolved_sources": resolved_sources,
            "launch_profile": launch_profile,
            "warnings": warnings,
            "proof_obligations": proof_obligations,
        }
    )


def _resolve_source(
    *,
    source: RecipeSourceSpec,
    catalog_store: CatalogStore,
) -> RecipeDatasetResolution:
    record: DatasetRecord | None = None
    notes = list(source.notes)

    if source.dataset_id:
        record = catalog_store.get_dataset(source.dataset_id)
    elif source.dataset_name and source.dataset_version:
        record = catalog_store.get_by_name_version(
            source.dataset_name,
            source.dataset_version,
        )
    elif source.dataset_name:
        record = catalog_store.get_latest_by_name(source.dataset_name)

    if record is not None:
        notes.append("catalog lineage located")
        return RecipeDatasetResolution(
            split=source.split,
            modality=source.modality,
            dataset_id=record.dataset_id,
            dataset_name=record.dataset_name,
            version=record.version,
            resolved=True,
            field_count=len(record.fields),
            primary_keys=record.primary_keys,
            partition_keys=record.partition_keys,
            source_uri=source.source_uri,
            connector_kind=source.connector_kind,
            notes=notes,
        )

    if source.source_uri:
        notes.append("external source declared without catalog registration")
    else:
        notes.append("dataset reference not found in catalog")

    return RecipeDatasetResolution(
        split=source.split,
        modality=source.modality,
        dataset_id=source.dataset_id,
        dataset_name=source.dataset_name,
        version=source.dataset_version,
        resolved=False,
        field_count=0,
        primary_keys=[],
        partition_keys=[],
        source_uri=source.source_uri,
        connector_kind=source.connector_kind,
        notes=notes,
    )


def _launcher_template(
    *,
    request: RecipeCompileRequest,
    manifest_path: str,
) -> str:
    trainer = "<trainer-entrypoint>"
    if request.distributed.engine == "local":
        return f"python3 -m {trainer} --recipe {manifest_path}"
    return (
        f"torchrun --nnodes {request.distributed.node_count} "
        f"--nproc_per_node {request.distributed.devices_per_node} "
        f"-m {trainer} --recipe {manifest_path}"
    )


def _compile_warnings(
    request: RecipeCompileRequest,
    resolved_sources: list[RecipeDatasetResolution],
) -> list[str]:
    warnings: list[str] = []
    unresolved = [item for item in resolved_sources if not item.resolved]
    if unresolved:
        warnings.append(
            f"{len(unresolved)} source lanes are not yet proven by the dataset catalog."
        )
    if request.model.adapter_kind in {"lora", "qlora"} and not request.model.target_modules:
        warnings.append(
            "Adapter-based tuning was requested without explicit target modules."
        )
    if request.distributed.engine == "deepspeed" and request.distributed.zero_stage == 0:
        warnings.append(
            "DeepSpeed was selected without a ZeRO stage; "
            "review whether local DDP is the truer fit."
        )
    if (
        any(source.split == "eval" for source in request.sources)
        and request.training.eval_interval_steps == 0
    ):
        warnings.append(
            "An evaluation split exists, but evaluation cadence is disabled."
        )
    if (
        any(source.modality in {"image", "video"} for source in request.sources)
        and not request.model.freeze_vision_tower
    ):
        warnings.append(
            "The vision tower is open for updates; confirm you have "
            "enough curated evidence before promotion."
        )
    return warnings


def _proof_obligations(
    request: RecipeCompileRequest,
    resolved_sources: list[RecipeDatasetResolution],
) -> list[str]:
    obligations = [
        "Export the manifest before execution and keep the export under version control.",
        "Keep one held-out evaluation lane with declared thresholds.",
        "Preserve source lineage for every split used in the recipe.",
    ]
    if request.distributed.engine == "deepspeed":
        obligations.append(
            "Pin the ZeRO stage and memory-offload choice beside observed memory envelopes."
        )
    if any(not item.resolved for item in resolved_sources):
        obligations.append(
            "Resolve unregistered sources into the dataset catalog before regulated deployment."
        )
    return obligations


def _launch_notes(
    request: RecipeCompileRequest,
    resolved_sources: list[RecipeDatasetResolution],
) -> list[str]:
    notes = [
        (
            f"{sum(1 for item in resolved_sources if item.resolved)} "
            f"of {len(resolved_sources)} source lanes are catalog-backed."
        ),
        "Verified commands are executable in this repository today.",
        "The launcher template is intentionally separate; it is a handoff "
        "surface for external runners, not a hidden claim.",
    ]
    if request.distributed.gradient_checkpointing:
        notes.append("Gradient checkpointing is enabled in the compiled topology.")
    if request.training.max_steps:
        notes.append(f"Execution is step-bounded at {request.training.max_steps} steps.")
    else:
        notes.append(f"Execution is epoch-bounded at {request.training.epochs} epochs.")
    return notes
