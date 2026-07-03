from __future__ import annotations

from collections import Counter
from typing import List

from .contracts import (
    BiasAssessmentRequest,
    BiasAssessmentResponse,
    BiasCategory,
    BiasFinding,
)

STAGE_LIBRARY = [
    ("collection", "ingestion and source selection"),
    ("consent", "permission, notice, and refusal handling"),
    ("sampling", "population coverage and cohort boundaries"),
    ("measurement", "sensor capture, signal quality, and instrument reliability"),
    ("labeling", "annotation and ground-truth framing"),
    ("feature_shaping", "normalization, compression, and proxy building"),
    ("retrieval", "indexing, ranking, and resurfacing"),
    ("evaluation", "benchmark choice and score interpretation"),
    ("interface", "display, ranking, and persuasive framing"),
    ("governance", "review, override, and accountability lanes"),
]

BIAS_FAMILIES = [
    ("exclusion", "people or cases disappear before the system ever sees them"),
    ("measurement", "the signal is read unevenly across groups or conditions"),
    ("proxy", "a substitute feature carries hidden demographic meaning"),
    ("aggregation", "different cohorts are compressed into one average"),
    ("temporal", "the population changes while the model keeps acting as if it did not"),
    ("escalation", "downstream automation amplifies a small early skew"),
]

SIGNAL_HINTS = {
    "exclusion": ["coverage", "missing", "omission", "dropout"],
    "measurement": ["sensor", "capture", "quality", "noise"],
    "proxy": ["zip", "device", "language", "network"],
    "aggregation": ["average", "merge", "collapse", "pooled"],
    "temporal": ["drift", "seasonality", "lag", "stale"],
    "escalation": ["ranking", "feedback", "reinforcement", "auto-route"],
}


def list_bias_taxonomy() -> List[BiasCategory]:
    categories: List[BiasCategory] = []
    category_index = 1
    for stage, entry_point in STAGE_LIBRARY:
        for family, description in BIAS_FAMILIES:
            categories.append(
                BiasCategory(
                    category_id=f"B{category_index:03d}",
                    stage=stage,
                    label=f"{stage.replace('_', ' ').title()} {family.title()} Bias",
                    entry_point=entry_point,
                    description=description,
                    signals=SIGNAL_HINTS[family] + [stage],
                )
            )
            category_index += 1
    return categories


def assess_bias(request: BiasAssessmentRequest) -> BiasAssessmentResponse:
    taxonomy = list_bias_taxonomy()
    active_stages = {stage.strip().lower() for stage in request.active_stages}
    observed_signals = {signal.strip().lower() for signal in request.observed_signals}
    data_categories = {category.strip().lower() for category in request.data_categories}
    notes = {note.strip().lower() for note in request.notes}
    evidence = observed_signals | data_categories | notes

    findings: List[BiasFinding] = []
    stage_summary: Counter[str] = Counter()

    for category in taxonomy:
        if category.stage not in active_stages:
            continue
        overlap = evidence.intersection(set(category.signals))
        if not overlap and not _stage_itself_is_high_risk(category.stage, data_categories):
            continue

        severity = _severity_for(category, overlap, data_categories)
        findings.append(
            BiasFinding(
                category_id=category.category_id,
                stage=category.stage,
                label=category.label,
                severity=severity,
                finding=_finding_text(category, overlap),
                mitigation=_mitigation_text(category),
            )
        )
        stage_summary[category.stage] += 1

    return BiasAssessmentResponse(
        system_name=request.system_name,
        total_categories=len(taxonomy),
        stage_summary=dict(stage_summary),
        findings=findings,
    )


def _stage_itself_is_high_risk(stage: str, data_categories: set[str]) -> bool:
    if stage == "measurement" and {"biometric", "audio", "video", "sensor"} & data_categories:
        return True
    if stage == "governance" and {"financial", "phi", "pii"} & data_categories:
        return True
    return False


def _severity_for(
    category: BiasCategory,
    overlap: set[str],
    data_categories: set[str],
) -> str:
    if (
        category.stage in {"governance", "feature_shaping"}
        and {"pii", "phi", "financial"} & data_categories
    ):
        return "critical"
    if len(overlap) >= 2:
        return "elevated"
    return "watch"


def _finding_text(category: BiasCategory, overlap: set[str]) -> str:
    if overlap:
        return (
            f"{category.label} is active because the current system signals include "
            f"{', '.join(sorted(overlap))}."
        )
    return f"{category.label} should be reviewed because this stage is active for sensitive data."


def _mitigation_text(category: BiasCategory) -> str:
    if category.stage == "collection":
        return "Measure who never enters the dataset before rebalancing what already arrived."
    if category.stage == "measurement":
        return (
            "Compare capture quality across cohorts before treating low signal "
            "as low importance."
        )
    if category.stage == "retrieval":
        return "Audit ranking and resurfacing pressure, not only the source corpus."
    if category.stage == "governance":
        return (
            "Require override lanes, auditable exceptions, and human review "
            "for sensitive routes."
        )
    return (
        "Inspect this stage directly, then save a narrower baseline before "
        "automating the next step."
    )
