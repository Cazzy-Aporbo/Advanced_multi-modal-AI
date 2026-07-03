from __future__ import annotations

import hashlib
from typing import List

from .config import Settings
from .contracts import (
    DatasetEvolutionRequest,
    DatasetEvolutionResponse,
    DatasetRecord,
    DatasetRegistrationRequest,
    SchemaChange,
)
from .rust_bridge import schema_fingerprint_from_payload


def register_dataset(
    request: DatasetRegistrationRequest,
    settings: Settings,
) -> DatasetRecord:
    canonical_schema, fingerprint = schema_fingerprint(
        dataset_name=request.dataset_name,
        fields=request.fields,
        partition_keys=request.partition_keys,
        primary_keys=request.primary_keys,
        settings=settings,
    )
    return DatasetRecord(
        dataset_name=request.dataset_name,
        owner=request.owner,
        version=request.version,
        modality=request.modality,
        partition_keys=request.partition_keys,
        primary_keys=request.primary_keys,
        fields=request.fields,
        fingerprint=fingerprint,
        canonical_schema=canonical_schema,
        tags=request.tags,
        notes=request.notes,
    )


def compare_dataset_schemas(
    current: DatasetRecord,
    candidate: DatasetEvolutionRequest,
) -> DatasetEvolutionResponse:
    current_fields = {field.name: field for field in current.fields}
    candidate_fields = {field.name: field for field in candidate.fields}

    additive_changes: List[SchemaChange] = []
    breaking_changes: List[SchemaChange] = []

    for field_name, field in candidate_fields.items():
        if field_name not in current_fields:
            additive_changes.append(
                SchemaChange(
                    field_name=field_name,
                    change_type="added",
                    detail=f"{field_name} was added to the candidate schema.",
                )
            )
            continue
        existing = current_fields[field_name]
        if field.dtype != existing.dtype:
            breaking_changes.append(
                SchemaChange(
                    field_name=field_name,
                    change_type="dtype_changed",
                    detail=f"{field_name} changed from {existing.dtype} to {field.dtype}.",
                )
            )
        if field.nullable != existing.nullable:
            change_list = (
                breaking_changes
                if existing.nullable and not field.nullable
                else additive_changes
            )
            change_list.append(
                SchemaChange(
                    field_name=field_name,
                    change_type="nullability_changed",
                    detail=(
                        f"{field_name} changed nullability from "
                        f"{existing.nullable} to {field.nullable}."
                    ),
                )
            )

    for field_name in current_fields:
        if field_name not in candidate_fields:
            breaking_changes.append(
                SchemaChange(
                    field_name=field_name,
                    change_type="removed",
                    detail=f"{field_name} is missing from the candidate schema.",
                )
            )

    return DatasetEvolutionResponse(
        dataset_name=current.dataset_name,
        current_version=current.version,
        candidate_version=candidate.candidate_version,
        compatible=not breaking_changes,
        additive_changes=additive_changes,
        breaking_changes=breaking_changes,
    )


def schema_fingerprint(
    dataset_name: str,
    fields,
    partition_keys: List[str],
    primary_keys: List[str],
    settings: Settings,
) -> tuple[str, str]:
    payload = {
        "dataset_name": dataset_name,
        "fields": [field.model_dump(mode="json") for field in fields],
        "partition_keys": partition_keys,
        "primary_keys": primary_keys,
    }
    rust_response = schema_fingerprint_from_payload(payload, settings)
    if rust_response is not None:
        return rust_response["canonical_schema"], rust_response["fingerprint"]

    canonical_schema = "dataset={};fields={};partition={};primary={}".format(
        dataset_name.strip().lower(),
        "|".join(
            f"{field.name.strip().lower()}:{field.dtype.strip().lower()}:"
            f"{'nullable' if field.nullable else 'required'}"
            for field in fields
        ),
        ",".join(value.strip().lower() for value in partition_keys),
        ",".join(value.strip().lower() for value in primary_keys),
    )
    fingerprint = hashlib.sha256(canonical_schema.encode("utf-8")).hexdigest()
    return canonical_schema, fingerprint
