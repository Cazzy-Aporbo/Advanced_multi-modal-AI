from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean

from .contracts import (
    DeliberationAssessmentRequest,
    DeliberationAssessmentResponse,
    EpistemicRiskIndicator,
    EpistemicRiskRequest,
    EpistemicRiskResponse,
    FeatureRepresentationCell,
    HarnessImprovementRequest,
    HarnessImprovementResponse,
    HarnessProposal,
    HarnessTraceRecord,
    HarnessWeaknessCluster,
    ResearchInfluenceBundle,
    ResearchInfluenceMechanism,
    ResearchInfluenceSource,
    ResearchRoadmapItem,
    TrustCalibrationFactor,
    TrustCalibrationRequest,
    TrustCalibrationResponse,
)


def build_research_influence_bundle(
    *,
    service_name: str,
    version: str,
    route_count: int,
    test_count: int,
) -> ResearchInfluenceBundle:
    sources = _sources()
    mechanisms = _mechanisms()
    feature_matrix = _feature_matrix()
    roadmap = _roadmap()
    return ResearchInfluenceBundle(
        service=service_name,
        version=version,
        route_count=route_count,
        test_count=test_count,
        source_count=len(sources),
        mechanism_count=len(mechanisms),
        feature_count=len(feature_matrix),
        sources=sources,
        mechanisms=mechanisms,
        feature_matrix=feature_matrix,
        roadmap=roadmap,
    )


def mine_harness_improvements(request: HarnessImprovementRequest) -> HarnessImprovementResponse:
    failed_traces = [trace for trace in request.traces if trace.outcome in {"fail", "blocked"}]
    grouped: dict[str, list[HarnessTraceRecord]] = defaultdict(list)
    for trace in failed_traces:
        tags = trace.failure_tags or ["unclassified-failure"]
        for tag in tags:
            grouped[_slug(tag)].append(trace)

    clusters: list[HarnessWeaknessCluster] = []
    proposals: list[HarnessProposal] = []
    for tag, traces in sorted(
        grouped.items(),
        key=lambda item: (-len(item[1]), item[0]),
    ):
        files = sorted({file for trace in traces for file in trace.files_touched})
        families = sorted({trace.task_family for trace in traces})
        trace_ids = [trace.trace_id for trace in traces]
        severity = _bounded(
            (len(traces) / max(1, len(failed_traces))) * 0.58
            + min(len(files), 8) * 0.035
            + min(len(families), 6) * 0.04
            + (0.1 if any(trace.outcome == "blocked" for trace in traces) else 0.0)
        )
        cluster_id = f"{request.base_harness_id}:{tag}"
        clusters.append(
            HarnessWeaknessCluster(
                cluster_id=cluster_id,
                failure_tag=tag,
                task_families=families,
                trace_ids=trace_ids,
                files_touched=files,
                support=len(traces),
                severity_score=severity,
                why_it_matters=_cluster_reason(tag, len(traces), families),
            )
        )
        proposal_status = (
            "promote" if len(traces) >= request.minimum_support and severity >= 0.28 else "hold"
        )
        commands = _dedupe(command for trace in traces for command in trace.verification_commands)
        if not commands:
            commands = ["python3 -m pytest -q"]
        if request.protected_invariants:
            commands = [*commands, "python3 scripts/build_runtime_proof_bundle.py"]
        proposals.append(
            HarnessProposal(
                proposal_id=f"proposal:{request.base_harness_id}:{tag}",
                cluster_id=cluster_id,
                status=proposal_status,
                change_shape=_proposal_shape(tag, files),
                acceptance_gate=commands,
                regression_tests=[
                    f"assert cluster `{tag}` no longer appears across {len(traces)} traces",
                    "assert proof export still contains route, test, and artifact counts",
                ],
                expected_behavior=(
                    "The next run should keep the successful traces stable while forcing "
                    "this repeated weakness to appear as a testable failure if it returns."
                ),
                rejection_reason=(
                    ""
                    if proposal_status == "promote"
                    else "Support is not high enough to change the harness yet."
                ),
            )
        )

    promoted = sum(1 for proposal in proposals if proposal.status == "promote")
    return HarnessImprovementResponse(
        base_harness_id=request.base_harness_id,
        trace_count=len(request.traces),
        failed_trace_count=len(failed_traces),
        promoted_proposal_count=promoted,
        clusters=clusters,
        proposals=proposals,
    )


def assess_deliberation(
    request: DeliberationAssessmentRequest,
) -> DeliberationAssessmentResponse:
    stance_counts = Counter(claim.stance for claim in request.claims)
    role_names = {claim.role.strip().lower() for claim in request.claims}
    missing_roles = [
        role for role in request.required_roles if role.strip().lower() not in role_names
    ]
    total_claims = len(request.claims)
    largest_stance = max(stance_counts.values(), default=0)
    disagreement = 1.0 - (largest_stance / max(1, total_claims))
    evidence_refs = {
        ref.strip() for claim in request.claims for ref in claim.evidence_refs if ref.strip()
    }
    average_uncertainty = mean([claim.uncertainty for claim in request.claims])
    recommendation = _deliberation_recommendation(
        disagreement=disagreement,
        evidence_ref_count=len(evidence_refs),
        missing_roles=missing_roles,
        average_uncertainty=average_uncertainty,
        role_count=len(role_names),
    )
    return DeliberationAssessmentResponse(
        decision_id=request.decision_id,
        domain=request.domain,
        role_count=len(role_names),
        stance_distribution=dict(sorted(stance_counts.items())),
        disagreement_score=round(disagreement, 4),
        evidence_ref_count=len(evidence_refs),
        missing_roles=missing_roles,
        recommendation=recommendation,
        next_questions=_deliberation_questions(
            domain=request.domain,
            disagreement=disagreement,
            missing_roles=missing_roles,
            evidence_ref_count=len(evidence_refs),
        ),
    )


def calibrate_trust(request: TrustCalibrationRequest) -> TrustCalibrationResponse:
    harm_scores = {"low": 1.0, "medium": 0.72, "high": 0.42, "critical": 0.25}
    raw_factors = [
        (
            "precision",
            request.precision,
            0.18,
            "How tightly the output can be checked against observable state.",
        ),
        (
            "human_control",
            request.human_control,
            0.22,
            "Whether a person can pause, review, and correct the route.",
        ),
        (
            "oversight",
            request.oversight,
            0.18,
            "Whether independent review is attached to the route.",
        ),
        (
            "validation_evidence",
            request.validation_evidence,
            0.22,
            "Whether the claim has test, receipt, or benchmark support.",
        ),
        (
            "reversibility",
            request.reversibility,
            0.13,
            "Whether a mistaken action can be unwound without hidden damage.",
        ),
        (
            "harm_fit",
            harm_scores[request.harm_level],
            0.07,
            "Higher-harm routes need a lower trust prior until reviewed.",
        ),
    ]
    factors = [
        TrustCalibrationFactor(
            factor=name,
            score=round(score, 4),
            weight=weight,
            contribution=round(score * weight, 4),
            note=note,
        )
        for name, score, weight, note in raw_factors
    ]
    score = round(sum(factor.contribution for factor in factors), 4)
    missing = [
        factor.factor for factor in factors if factor.factor != "harm_fit" and factor.score < 0.58
    ]
    band = "high" if score >= 0.75 else "medium" if score >= 0.48 else "low"
    review_required = bool(
        score < 0.75
        or missing
        or (
            request.harm_level in {"high", "critical"}
            and min(request.human_control, request.oversight, request.validation_evidence) < 0.72
        )
    )
    return TrustCalibrationResponse(
        route=request.route,
        purpose=request.purpose,
        score=score,
        band=band,
        review_required=review_required,
        factors=factors,
        missing_controls=missing,
    )


def assess_epistemic_risk(request: EpistemicRiskRequest) -> EpistemicRiskResponse:
    evidence = request.evidence
    total = len(evidence)
    perspectives = {item.perspective.strip().lower() for item in evidence if item.perspective}
    source_types = {item.source_type for item in evidence}
    claim_counts = Counter(_claim_fingerprint(item.claim) for item in evidence)
    repeated_items = sum(count - 1 for count in claim_counts.values() if count > 1)
    unsupported_certainty = sum(
        1 for item in evidence if item.confidence >= 0.82 and not item.uncertainty_visible
    )
    human_review_count = sum(1 for item in evidence if item.human_generated)
    stale_count = sum(1 for item in evidence if item.age_days > 180)

    diversity_gap = 1.0 - min(1.0, (len(perspectives) + len(source_types)) / 7.0)
    repetition_pressure = repeated_items / max(1, total)
    overcertainty_pressure = unsupported_certainty / max(1, total)
    offloading_pressure = 0.0 if human_review_count else 1.0
    freshness_pressure = stale_count / max(1, total)
    score = _bounded(
        diversity_gap * 0.24
        + repetition_pressure * 0.22
        + overcertainty_pressure * 0.24
        + offloading_pressure * 0.18
        + freshness_pressure * 0.12
    )
    indicators = [
        EpistemicRiskIndicator(
            indicator_id="evidence-diversity",
            label="Evidence diversity",
            score=round(diversity_gap, 4),
            evidence=(
                f"{len(perspectives)} perspectives and {len(source_types)} source "
                f"types appear across {total} items."
            ),
            correction="Add a second independent source class or dissenting review before reuse.",
        ),
        EpistemicRiskIndicator(
            indicator_id="unsupported-certainty",
            label="Unsupported certainty",
            score=round(overcertainty_pressure, 4),
            evidence=f"{unsupported_certainty} high-confidence items hide uncertainty.",
            correction="Require uncertainty fields beside every high-confidence claim.",
        ),
        EpistemicRiskIndicator(
            indicator_id="repetition-pressure",
            label="Repetition pressure",
            score=round(repetition_pressure, 4),
            evidence=f"{repeated_items} repeated claims were found after normalization.",
            correction=(
                "Cluster repeated claims and ask for a new measurement, "
                "not another paraphrase."
            ),
        ),
        EpistemicRiskIndicator(
            indicator_id="human-review-gap",
            label="Human review gap",
            score=round(offloading_pressure, 4),
            evidence=f"{human_review_count} evidence items were marked as human-generated.",
            correction="Keep one non-delegable human check before decision-grade use.",
        ),
        EpistemicRiskIndicator(
            indicator_id="freshness",
            label="Freshness",
            score=round(freshness_pressure, 4),
            evidence=f"{stale_count} evidence items are older than 180 days.",
            correction="Refresh old sources or mark their domain limits explicitly.",
        ),
    ]
    return EpistemicRiskResponse(
        assessment_id=request.assessment_id,
        domain=request.domain,
        band=_risk_band(score),
        score=round(score, 4),
        evidence_count=total,
        perspective_count=len(perspectives),
        indicators=indicators,
        non_delegable_checks=[
            "Name what the system did not observe.",
            "Keep uncertainty visible beside any confident answer.",
            "Require a human reviewer for high-impact or stale evidence.",
        ],
    )


def _sources() -> list[ResearchInfluenceSource]:
    return [
        ResearchInfluenceSource(
            source_id="self_harness_2026",
            title="Self-Harness: Harnesses That Improve Themselves",
            authors=[
                "Hangfan Zhang",
                "Shao Zhang",
                "Kangcong Li",
                "Chen Zhang",
                "Yang Chen",
                "Yiqun Zhang",
                "Lei Bai",
                "Shuyue Hu",
            ],
            year=2026,
            page_count=19,
            field="agent harness improvement",
            mechanisms=[
                "weakness mining from execution traces",
                "minimal harness proposal",
                "regression-gated promotion",
            ],
            repository_translation=(
                "Turn failed or sparse proof lanes into explicit improvement candidates, "
                "then accept only changes that survive tests and exported evidence."
            ),
        ),
        ResearchInfluenceSource(
            source_id="legal_deliberation_2026",
            title="Investigating Multi-Agent Deliberation in Law",
            authors=["Cor Steging", "Ludi van Leeuwen", "Tadeusz Zbiegien"],
            year=2026,
            page_count=11,
            field="legal reasoning and multi-agent deliberation",
            mechanisms=[
                "multi-agent deliberation",
                "3-ply adversarial argument",
                "role-diverse critique",
            ],
            repository_translation=(
                "Represent high-stakes interpretations as competing viewpoints before "
                "collapsing them into one route, verdict, or recommendation."
            ),
        ),
        ResearchInfluenceSource(
            source_id="trust_warroom_2026",
            title="AI, Trust, and the War Room: Evidence from a Conjoint Experiment",
            authors=["Paul Lushenko"],
            year=2026,
            page_count=24,
            field="human-machine trust and oversight",
            mechanisms=[
                "trust calibration",
                "human control",
                "oversight sensitivity",
                "mission and harm tradeoff",
            ],
            repository_translation=(
                "Expose evidence strength, human review posture, intended use, and oversight "
                "signals directly beside model or diagnostic output."
            ),
        ),
        ResearchInfluenceSource(
            source_id="epistemic_risks_2026",
            title="AI Epistemic Risks: Emerging Mechanisms and Evidence",
            authors=[
                "Mick Yang",
                "Stephen Casper",
                "Jonathan Stray",
                "Jasmine Li",
                "Cameron Jones",
                "Anna Gausen",
                "Natasha Jaques",
                "Brian Christian",
                "Balint Gyevnar",
                "Hannah Rose Kirk",
                "Zhonghao He",
                "Dan Zhao",
                "Siao Si Looi",
                "Joshua Levy",
                "Kobi Hackenburg",
                "Elizabeth Seger",
                "Matt Kowal",
                "Michelle Malonza",
                "Luke Hewitt",
                "Hause Lin",
                "Maarten Sap",
                "Dylan Hadfield-Menell",
                "Thomas H. Costello",
                "Reihaneh Rabbany",
                "Jean-Francois Godbout",
                "David G. Rand",
                "Atoosa Kasirzadeh",
                "Gordon Pennycook",
                "Yoshua Bengio",
                "Kellin Pelrine",
            ],
            year=2026,
            page_count=97,
            field="epistemic risk and cognitive resilience",
            mechanisms=[
                "persuasion and manipulation",
                "cognitive offloading",
                "feedback loops and lock-in",
                "epistemic diversity",
            ],
            repository_translation=(
                "Measure when a system narrows evidence, repeats itself, reduces human "
                "checking, or makes uncertainty harder to see."
            ),
        ),
    ]


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def _slug(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-").replace(" ", "-")
    return "".join(character for character in normalized if character.isalnum() or character == "-")


def _dedupe(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if cleaned and cleaned not in seen:
            result.append(cleaned)
            seen.add(cleaned)
    return result


def _cluster_reason(tag: str, support: int, families: list[str]) -> str:
    family_text = ", ".join(families[:3]) or "one task family"
    return (
        f"`{tag}` appears across {support} failed or blocked traces in {family_text}. "
        "A repeated trace pattern is stronger than an isolated note because it can be "
        "turned into a regression fixture."
    )


def _proposal_shape(tag: str, files: list[str]) -> str:
    file_text = ", ".join(files[:3]) if files else "the affected route or proof export"
    return (
        f"Add a narrow fixture for `{tag}`, bind it to {file_text}, and promote the "
        "change only when the proof bundle regenerates without losing existing artifacts."
    )


def _deliberation_recommendation(
    *,
    disagreement: float,
    evidence_ref_count: int,
    missing_roles: list[str],
    average_uncertainty: float,
    role_count: int,
) -> str:
    if evidence_ref_count == 0 and disagreement >= 0.45:
        return "block"
    if missing_roles or disagreement >= 0.5:
        return "escalate"
    if role_count < 3 or average_uncertainty >= 0.58 or evidence_ref_count < role_count:
        return "review"
    return "decide"


def _deliberation_questions(
    *,
    domain: str,
    disagreement: float,
    missing_roles: list[str],
    evidence_ref_count: int,
) -> list[str]:
    questions = [
        f"What evidence would change the current {domain} decision?",
        "Which claim is still relying on interpretation rather than measurement?",
    ]
    if missing_roles:
        questions.append(f"Which view is missing: {', '.join(missing_roles)}?")
    if disagreement >= 0.4:
        questions.append("Can the disagreement be reduced to one observable test?")
    if evidence_ref_count == 0:
        questions.append("What record, receipt, or benchmark supports this route?")
    return questions


def _claim_fingerprint(value: str) -> str:
    words = [
        word.strip(".,;:!?()[]{}\"'").lower()
        for word in value.split()
        if len(word.strip(".,;:!?()[]{}\"'")) > 3
    ]
    return " ".join(words[:12]) or value.strip().lower()


def _risk_band(score: float) -> str:
    if score >= 0.72:
        return "critical"
    if score >= 0.5:
        return "elevated"
    if score >= 0.28:
        return "watch"
    return "low"


def _mechanisms() -> list[ResearchInfluenceMechanism]:
    return [
        ResearchInfluenceMechanism(
            mechanism_id="weakness_mining",
            label="Weakness mining from traces",
            source_ids=["self_harness_2026"],
            repo_files=[
                "src/advanced_multimodal_ai/execution_journal.py",
                "src/advanced_multimodal_ai/repository_growth.py",
                "src/advanced_multimodal_ai/research_influence.py",
                "proof/execution-journal.md",
            ],
            runtime_routes=[
                "/v1/execution/journal",
                "/v1/growth/snapshot",
                "/v1/research/harness-improvement",
            ],
            implementation_status="active",
            score=86,
            why_it_matters=(
                "The repo can inspect traces and cluster repeated failures into concrete "
                "improvement proposals with acceptance gates."
            ),
            next_test="Keep the harness-improvement endpoint tied to repeated failed traces.",
            visual_surface="research-influence.html#mechanisms",
        ),
        ResearchInfluenceMechanism(
            mechanism_id="regression_gated_change",
            label="Regression-gated change promotion",
            source_ids=["self_harness_2026"],
            repo_files=["Makefile", ".github/workflows/ci.yml", "scripts/run_acceptance_spine.py"],
            runtime_routes=["/v1/proof/bundle", "/v1/readiness/report"],
            implementation_status="active",
            score=84,
            why_it_matters=(
                "Improvements become credible when they are promoted through tests, proof "
                "exports, and generated clients together."
            ),
            next_test=(
                "Add an acceptance assertion that every public proof page has a "
                "matching export script."
            ),
            visual_surface="research-influence.html#roadmap",
        ),
        ResearchInfluenceMechanism(
            mechanism_id="deliberative_disagreement",
            label="Deliberative disagreement matrix",
            source_ids=["legal_deliberation_2026"],
            repo_files=[
                "src/advanced_multimodal_ai/industry_profiles.py",
                "src/advanced_multimodal_ai/bias_taxonomy.py",
                "src/advanced_multimodal_ai/research_influence.py",
            ],
            runtime_routes=[
                "/v1/industries/profiles",
                "/v1/bias/assess",
                "/v1/research/deliberation/assess",
            ],
            implementation_status="active",
            score=77,
            why_it_matters=(
                "Some tasks need structured disagreement before a single answer is safe to "
                "present, especially legal, healthcare, employment, and safety domains."
            ),
            next_test="Expand fixtures with more role mixes and evidence sparsity patterns.",
            visual_surface="research-influence.html#features",
        ),
        ResearchInfluenceMechanism(
            mechanism_id="trust_calibration",
            label="Trust calibration with oversight",
            source_ids=["trust_warroom_2026"],
            repo_files=[
                "src/advanced_multimodal_ai/readiness.py",
                "src/advanced_multimodal_ai/edge_gateway.py",
                "src/advanced_multimodal_ai/industrial_diagnostics/engine.py",
                "src/advanced_multimodal_ai/research_influence.py",
            ],
            runtime_routes=[
                "/v1/readiness/report",
                "/v1/edge/evaluate",
                "/v1/industrial/diagnose",
                "/v1/research/trust/calibrate",
            ],
            implementation_status="active",
            score=87,
            why_it_matters=(
                "Users trust systems differently depending on purpose, precision, oversight, "
                "and human control. Those factors need visible state, not hidden prose."
            ),
            next_test=(
                "Score every high-impact response for oversight, human review, "
                "and evidence freshness."
            ),
            visual_surface="research-influence.html#mechanisms",
        ),
        ResearchInfluenceMechanism(
            mechanism_id="epistemic_friction",
            label="Epistemic friction against over-delegation",
            source_ids=["epistemic_risks_2026"],
            repo_files=[
                "src/advanced_multimodal_ai/music_truth.py",
                "src/advanced_multimodal_ai/research_surfaces.py",
                "src/advanced_multimodal_ai/operator_surfaces.py",
                "src/advanced_multimodal_ai/research_influence.py",
            ],
            runtime_routes=[
                "/v1/music/drift",
                "/v1/research/surfaces",
                "/v1/operators/surfaces",
                "/v1/research/epistemic-risk/assess",
            ],
            implementation_status="active",
            score=82,
            why_it_matters=(
                "Interfaces should help people keep checking, comparing, and asking better "
                "questions instead of quietly delegating judgment."
            ),
            next_test=(
                "Add more domain fixtures for stale evidence, repeated claims, "
                "and missing human review."
            ),
            visual_surface="research-influence.html#roadmap",
        ),
        ResearchInfluenceMechanism(
            mechanism_id="feedback_loop_lockin",
            label="Feedback-loop and lock-in monitoring",
            source_ids=["epistemic_risks_2026"],
            repo_files=[
                "src/advanced_multimodal_ai/music_truth.py",
                "src/advanced_multimodal_ai/drift.py",
                "src/advanced_multimodal_ai/repository_pulse.py",
            ],
            runtime_routes=["/v1/music/drift", "/v1/drift/check", "/v1/repository/pulse"],
            implementation_status="partial",
            score=69,
            why_it_matters=(
                "Homogenization can look like stability until the system has already stopped "
                "seeing important variation."
            ),
            next_test=(
                "Add longitudinal drift fixtures for repetition, source narrowing, "
                "and language collapse."
            ),
            visual_surface="research-influence.html#features",
        ),
    ]


def _feature_matrix() -> list[FeatureRepresentationCell]:
    return [
        FeatureRepresentationCell(
            feature_id="music_warehouse",
            label="Music feature warehouse",
            source_mechanisms=["feedback_loop_lockin", "epistemic_friction"],
            evidence_files=[
                "proof/music-observatory.md",
                "src/advanced_multimodal_ai/music_truth.py",
            ],
            runtime_routes=["/v1/music/snapshot", "/v1/music/drift"],
            representation_score=78,
            representation_gap=(
                "Needs more public fixture variety across language, region, "
                "instrumentation, and production style."
            ),
            next_six_month_problem=(
                "Detect when recommendation data becomes polished, repetitive, "
                "or regionally narrow."
            ),
            visual_treatment="Segment clusters with drift bands and source-diversity counters.",
        ),
        FeatureRepresentationCell(
            feature_id="industrial_diagnostics",
            label="Industrial diagnostics",
            source_mechanisms=["trust_calibration", "regression_gated_change"],
            evidence_files=[
                "proof/industrial-diagnostics.md",
                "src/advanced_multimodal_ai/industrial_diagnostics/explainability/fault_graph.py",
            ],
            runtime_routes=["/v1/industrial/diagnose", "/v1/industrial/model-check"],
            representation_score=83,
            representation_gap="Needs more machine families and noisy sensor fixtures.",
            next_six_month_problem=(
                "Show how safety state, sensor uncertainty, and restart permission "
                "change under field noise."
            ),
            visual_treatment="Fault graph from signal to diagnosis to compliance to action.",
        ),
        FeatureRepresentationCell(
            feature_id="edge_gateway",
            label="Edge review and boundary scoring",
            source_mechanisms=["trust_calibration"],
            evidence_files=["proof/edge-topology.md", "src/advanced_multimodal_ai/edge_gateway.py"],
            runtime_routes=["/v1/edge/evaluate", "/v1/edge/topology"],
            representation_score=74,
            representation_gap=(
                "Needs scenario fixtures for different oversight and human-control "
                "postures."
            ),
            next_six_month_problem=(
                "Represent when a route should pause for review without freezing "
                "useful low-risk work."
            ),
            visual_treatment="Boundary map with route action, risk bands, and review state.",
        ),
        FeatureRepresentationCell(
            feature_id="industry_profiles",
            label="Industry transfer profiles",
            source_mechanisms=["deliberative_disagreement", "trust_calibration"],
            evidence_files=[
                "proof/industry-profiles.md",
                "src/advanced_multimodal_ai/industry_profiles.py",
            ],
            runtime_routes=["/v1/industries/profiles"],
            representation_score=70,
            representation_gap="Needs role-specific review views for each high-risk domain.",
            next_six_month_problem=(
                "Show how the same runtime lane changes when the audience is "
                "clinical, legal, educational, or operational."
            ),
            visual_treatment=(
                "Domain cards with route anchors, proof files, and disagreement prompts."
            ),
        ),
        FeatureRepresentationCell(
            feature_id="repository_growth",
            label="Repository growth and contribution health",
            source_mechanisms=["weakness_mining", "regression_gated_change"],
            evidence_files=["proof/repository-growth.md", "CONTRIBUTING.md"],
            runtime_routes=["/v1/growth/snapshot"],
            representation_score=76,
            representation_gap=(
                "Needs time-series snapshots after GitHub traffic becomes available."
            ),
            next_six_month_problem=(
                "Separate real adoption signals from vanity metrics and stale "
                "publication artifacts."
            ),
            visual_treatment="Contribution health, proof freshness, and traffic trend panels.",
        ),
        FeatureRepresentationCell(
            feature_id="research_surfaces",
            label="Research surfaces and model cards",
            source_mechanisms=["epistemic_friction", "deliberative_disagreement"],
            evidence_files=["proof/research-surfaces.md", "model-observatory.html"],
            runtime_routes=["/v1/research/surfaces", "/v1/research/models"],
            representation_score=72,
            representation_gap=(
                "Needs clearer disagreement and uncertainty fields for each model card."
            ),
            next_six_month_problem=(
                "Make model comparison increase human understanding rather than "
                "compressing judgment into one score."
            ),
            visual_treatment="Model cards with open questions, evidence class, and next proof.",
        ),
    ]


def _roadmap() -> list[ResearchRoadmapItem]:
    return [
        ResearchRoadmapItem(
            horizon="0-30 days",
            label="Trace-ranked improvement backlog",
            problem=(
                "The repo has proof exports but does not yet rank repeated weaknesses "
                "automatically."
            ),
            engineering_response=(
                "Mine execution journal failures and sparse proof lanes into scored "
                "improvement candidates."
            ),
            proof_to_add="proof/research-influence.md plus a regression test for backlog ordering.",
        ),
        ResearchRoadmapItem(
            horizon="30-60 days",
            label="Role-balanced review fixtures",
            problem="Some domains need structured disagreement before a final route is trusted.",
            engineering_response=(
                "Add advocate, skeptic, and reviewer fixtures to bias, industry, "
                "and diagnostics lanes."
            ),
            proof_to_add="A fixture bundle showing where roles agree, disagree, and defer.",
        ),
        ResearchRoadmapItem(
            horizon="60-120 days",
            label="Epistemic drift counters",
            problem=(
                "A system can look stable while sources narrow, phrasing repeats, "
                "or humans stop checking."
            ),
            engineering_response=(
                "Add diversity, repetition, uncertainty, and human-review counters "
                "across proof surfaces."
            ),
            proof_to_add=(
                "A generated epistemic-risk report tied to music, research, "
                "and operator routes."
            ),
        ),
        ResearchRoadmapItem(
            horizon="120-180 days",
            label="Oversight-sensitive route policy",
            problem=(
                "Trust depends on purpose, control, precision, and oversight, "
                "not model output alone."
            ),
            engineering_response=(
                "Attach oversight posture and human-control state to high-impact "
                "route responses."
            ),
            proof_to_add=(
                "A readiness export showing which high-impact routes have adequate "
                "review state."
            ),
        ),
    ]
