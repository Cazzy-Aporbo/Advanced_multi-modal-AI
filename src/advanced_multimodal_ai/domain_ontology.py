from __future__ import annotations

import re
from collections import OrderedDict
from typing import Dict, Iterable, List

from .contracts import (
    DomainArtifact,
    GeometricConstraint,
    OntologyEntity,
    OntologyIngestRequest,
    OntologyRelation,
    OntologySnapshot,
)

ROUTE_PATTERN = re.compile(r"/[a-zA-Z0-9_./-]+")
TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")

ACTION_WORDS = {
    "create",
    "delete",
    "export",
    "import",
    "read",
    "route",
    "share",
    "store",
    "sync",
    "transfer",
    "update",
    "write",
}

DATA_CATEGORY_WORDS = {"pii", "phi", "financial", "biometric", "customer", "employee"}
REGION_WORDS = {"eu", "us", "uk", "apac", "ca", "sg", "ph"}


def ingest_domain_ontology(request: OntologyIngestRequest) -> OntologySnapshot:
    entities: "OrderedDict[str, OntologyEntity]" = OrderedDict()
    relations: List[OntologyRelation] = []
    constraints: List[GeometricConstraint] = []
    notes: List[str] = []

    _ensure_entity(
        entities,
        label=request.tenant_id,
        kind="domain",
        control_depth="context",
    )

    for artifact in request.artifacts:
        _extract_surface_entities(artifact, entities, relations)
        if artifact.control_depth == "governance":
            constraints.extend(_compile_governance_constraints(artifact, request.zone_cells))

    if not constraints:
        notes.append(
            "No enforceable governance clauses were compiled from the supplied artifacts."
        )

    return OntologySnapshot(
        tenant_id=request.tenant_id,
        label=request.label,
        entities=list(entities.values()),
        relations=relations,
        constraints=constraints,
        zone_cells=request.zone_cells,
        notes=notes,
    )


def _extract_surface_entities(
    artifact: DomainArtifact,
    entities: "OrderedDict[str, OntologyEntity]",
    relations: List[OntologyRelation],
) -> None:
    artifact_token = _ensure_entity(
        entities,
        label=artifact.title,
        kind="dataset" if artifact.artifact_type == "data_dictionary" else "domain",
        control_depth=artifact.control_depth,
    )

    routes = sorted(set(ROUTE_PATTERN.findall(artifact.body)))
    for route in routes:
        route_token = _ensure_entity(
            entities,
            label=route,
            kind="api",
            control_depth=artifact.control_depth,
        )
        relations.append(
            OntologyRelation(
                source_id=artifact_token.entity_id,
                relation="describes",
                target_id=route_token.entity_id,
                rationale=f"{artifact.title} contains the route {route}.",
            )
        )

    for token in _interesting_tokens(artifact.body, artifact.tags):
        kind = _token_kind(token)
        token_entity = _ensure_entity(
            entities,
            label=token,
            kind=kind,
            control_depth=artifact.control_depth,
        )
        relations.append(
            OntologyRelation(
                source_id=artifact_token.entity_id,
                relation="names",
                target_id=token_entity.entity_id,
                rationale=f"{artifact.title} names {token}.",
            )
        )


def _compile_governance_constraints(
    artifact: DomainArtifact,
    zone_cells: Dict[str, List[str]],
) -> List[GeometricConstraint]:
    body = artifact.body.lower()
    categories = [word for word in DATA_CATEGORY_WORDS if word in body]
    routes = ROUTE_PATTERN.findall(artifact.body)
    subject = routes[0] if routes else artifact.title
    constraints: List[GeometricConstraint] = []

    if "encrypt" in body:
        constraints.append(
            GeometricConstraint(
                policy_name=f"{artifact.title} encryption requirement",
                source_artifact_id=artifact.artifact_id,
                action="require_encryption",
                subject=subject,
                data_categories=categories,
                authority_basis=_authority_basis(body),
                notes=["The artifact requires encrypted transport or storage."],
            )
        )

    if "review" in body or "approval" in body:
        constraints.append(
            GeometricConstraint(
                policy_name=f"{artifact.title} review requirement",
                source_artifact_id=artifact.artifact_id,
                action="require_review",
                subject=subject,
                data_categories=categories,
                authority_basis=_authority_basis(body),
                notes=["The artifact calls for a reviewed or approved handling path."],
            )
        )

    if "eu" in body and "us" in body and _contains_prohibition(body):
        constraints.append(
            GeometricConstraint(
                policy_name=f"{artifact.title} regional transfer block",
                source_artifact_id=artifact.artifact_id,
                action="block",
                subject=subject,
                from_zone=_zone_reference("eu", zone_cells),
                to_zone=_zone_reference("us", zone_cells),
                data_categories=categories or ["pii"],
                authority_basis=_authority_basis(body) or ["regional-transfer"],
                notes=["The artifact prohibits the route from moving data from the EU to the US."],
            )
        )

    if "hipaa" in body and ("phi" in body or "health" in body):
        constraints.append(
            GeometricConstraint(
                policy_name=f"{artifact.title} PHI regional pin",
                source_artifact_id=artifact.artifact_id,
                action="pin_region",
                subject=subject,
                from_zone=_zone_reference("us", zone_cells),
                to_zone=_zone_reference("us", zone_cells),
                data_categories=["phi"],
                authority_basis=["hipaa"],
                notes=[
                    "The artifact keeps protected health information "
                    "inside its declared care region."
                ],
            )
        )

    if "gdpr" in body and "pii" in body:
        constraints.append(
            GeometricConstraint(
                policy_name=f"{artifact.title} personal-data review lane",
                source_artifact_id=artifact.artifact_id,
                action="require_review",
                subject=subject,
                data_categories=["pii"],
                authority_basis=["gdpr"],
                notes=["The artifact requires a reviewed lane for personal data handling."],
            )
        )

    return constraints


def _ensure_entity(
    entities: "OrderedDict[str, OntologyEntity]",
    label: str,
    kind: str,
    control_depth: str,
) -> OntologyEntity:
    entity_id = f"{kind}:{_normalize(label)}"
    if entity_id not in entities:
        entities[entity_id] = OntologyEntity(
            entity_id=entity_id,
            label=label,
            kind=kind,
            control_depth=control_depth,
        )
    return entities[entity_id]


def _interesting_tokens(body: str, tags: Iterable[str]) -> List[str]:
    tokens = set(tag.lower() for tag in tags)
    tokens.update(token.lower() for token in TOKEN_PATTERN.findall(body))
    return sorted(
        token
        for token in tokens
        if token not in {"shall", "must", "with", "from", "into", "data", "route"}
    )


def _token_kind(token: str) -> str:
    if token in ACTION_WORDS:
        return "action"
    if token in REGION_WORDS:
        return "jurisdiction"
    if token in DATA_CATEGORY_WORDS:
        return "object"
    return "object"


def _authority_basis(body: str) -> List[str]:
    basis: List[str] = []
    for marker in ("gdpr", "hipaa", "sec", "sox", "pci", "contract"):
        if marker in body:
            basis.append(marker)
    return basis


def _contains_prohibition(body: str) -> bool:
    return any(marker in body for marker in ("must not", "shall not", "forbid", "prohibit"))


def _zone_reference(region: str, zone_cells: Dict[str, List[str]]) -> str:
    cells = zone_cells.get(region.upper()) or zone_cells.get(region.lower()) or []
    if cells:
        return cells[0]
    return f"zone::{region.lower()}"


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
