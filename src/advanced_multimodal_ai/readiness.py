from __future__ import annotations

from .contracts import (
    ReadinessBoundary,
    ReadinessCheck,
    ReadinessPosture,
    ReadinessReport,
    RecipeRecord,
    RuntimeAttestationResponse,
    RuntimeProofBundle,
)


def build_readiness_report(
    *,
    attestation: RuntimeAttestationResponse,
    proof_bundle: RuntimeProofBundle,
    recipes: list[RecipeRecord],
) -> ReadinessReport:
    present_artifacts = [
        artifact for artifact in proof_bundle.verification_artifacts if artifact.status == "present"
    ]
    resolved_recipe_count = sum(
        1 for recipe in recipes if recipe.resolved_sources and all(
            source.resolved for source in recipe.resolved_sources
        )
    )

    checks = [
        ReadinessCheck(
            name="contract_surface",
            state="pass" if proof_bundle.route_count >= 45 else "watch",
            detail=f"{proof_bundle.route_count} public runtime surfaces are exported.",
        ),
        ReadinessCheck(
            name="verification_depth",
            state="pass" if proof_bundle.test_count >= 25 else "watch",
            detail=f"{proof_bundle.test_count} tests are currently counted in the proof bundle.",
        ),
        ReadinessCheck(
            name="artifact_evidence",
            state=(
                "pass"
                if len(present_artifacts) == proof_bundle.verification_artifact_count
                else "fail"
            ),
            detail=(
                f"{len(present_artifacts)} of {proof_bundle.verification_artifact_count} "
                "declared verification artifacts are present."
            ),
        ),
        ReadinessCheck(
            name="connector_coverage",
            state=(
                "pass"
                if "s3_parquet" in proof_bundle.connector_kinds
                and "web_html" in proof_bundle.connector_kinds
                else "watch"
            ),
            detail=", ".join(proof_bundle.connector_kinds),
        ),
        ReadinessCheck(
            name="connector_evidence",
            state=(
                "pass"
                if attestation.store_counts.get("connector_runs", 0) >= 2
                else "watch"
            ),
            detail=(
                f"{attestation.store_counts.get('connector_runs', 0)} persisted connector runs "
                "are recorded."
            ),
        ),
        ReadinessCheck(
            name="recipe_resolution",
            state="pass" if resolved_recipe_count >= 1 else "watch",
            detail=(
                f"{resolved_recipe_count} of {len(recipes)} compiled recipes have "
                "fully resolved source evidence."
            ),
        ),
        ReadinessCheck(
            name="governance_evidence",
            state=(
                "pass"
                if attestation.store_counts.get("drift_baselines", 0) >= 1
                and attestation.store_counts.get("ontology_snapshots", 0) >= 1
                and attestation.store_counts.get("pipeline_runs", 0) >= 1
                else "watch"
            ),
            detail=(
                "drift baselines="
                f"{attestation.store_counts.get('drift_baselines', 0)}, "
                "ontology snapshots="
                f"{attestation.store_counts.get('ontology_snapshots', 0)}, "
                "pipeline runs="
                f"{attestation.store_counts.get('pipeline_runs', 0)}"
            ),
        ),
        ReadinessCheck(
            name="stewardship_surface",
            state=(
                "pass"
                if attestation.store_counts.get("lifecycle_policies", 0) >= 1
                and attestation.store_counts.get("change_controls", 0) >= 1
                and attestation.store_counts.get("supply_chain_snapshots", 0) >= 1
                else "watch"
            ),
            detail=(
                "lifecycle policies="
                f"{attestation.store_counts.get('lifecycle_policies', 0)}, "
                "change controls="
                f"{attestation.store_counts.get('change_controls', 0)}, "
                "supply snapshots="
                f"{attestation.store_counts.get('supply_chain_snapshots', 0)}"
            ),
        ),
    ]

    blockers = [
        check.detail for check in checks if check.state == "fail"
    ]

    watch_count = sum(1 for check in checks if check.state == "watch")
    posture: ReadinessPosture
    if blockers:
        posture = "needs_buildout"
    elif watch_count:
        posture = "needs_evidence"
    else:
        posture = "review_ready"

    boundaries = [
        ReadinessBoundary(
            area="distributed execution",
            detail=(
                "Compiled recipes describe launch topology and checked manifest export, "
                "but an external trainer still executes the run."
            ),
        ),
        ReadinessBoundary(
            area="cloud credentials",
            detail=(
                "The S3 Parquet lane depends on caller-managed credentials and does not "
                "store secrets inside the runtime."
            ),
        ),
        ReadinessBoundary(
            area="public web intake",
            detail=(
                "The web_html lane is limited to public pages, domain allowlists, "
                "robots-aware fetch rules, and byte-capped extraction."
            ),
        ),
        ReadinessBoundary(
            area="serving topology",
            detail=(
                "The repository proves a single-service runtime edge with supporting stores, "
                "not a hidden multi-cluster control plane."
            ),
        ),
        ReadinessBoundary(
            area="data retirement",
            detail=(
                "Lifecycle, change-control, and supply-chain surfaces document review, "
                "retention, and removal intent, but external schedulers still carry out "
                "the physical delete or archive operation."
            ),
        ),
    ]

    return ReadinessReport(
        posture=posture,
        route_count=proof_bundle.route_count,
        test_count=proof_bundle.test_count,
        verification_artifact_count=proof_bundle.verification_artifact_count,
        connector_kinds=proof_bundle.connector_kinds,
        resolved_recipe_count=resolved_recipe_count,
        compiled_recipe_count=len(recipes),
        checks=checks,
        blockers=blockers,
        boundaries=boundaries,
    )
