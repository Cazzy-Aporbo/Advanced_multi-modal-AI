from __future__ import annotations

from statistics import mean

from .contracts import (
    BenchmarkStageResult,
    CymaticBand,
    CymaticMetric,
    CymaticNarrative,
    CymaticStageCard,
    CymaticSurfaceBundle,
    ExecutionJournalSummary,
    ReferenceBenchmarkResult,
    RepositoryPulse,
    ResearchSurfaceBundle,
)


def build_cymatic_surface_bundle(
    *,
    research_bundle: ResearchSurfaceBundle,
    repository_pulse: RepositoryPulse,
    benchmark: ReferenceBenchmarkResult,
    execution_journal: ExecutionJournalSummary,
) -> CymaticSurfaceBundle:
    live_scores = [lane.live_score / 100 for lane in repository_pulse.lanes]
    average_live_score = mean(live_scores) if live_scores else 0.62
    warning_load = sum(lane.warning_count for lane in repository_pulse.lanes)
    connector_reach = min(1.0, research_bundle.summary.connector_kind_count / 8)
    question_pressure = min(1.0, research_bundle.summary.open_question_count / 8)
    replay_bonus = 0.16 if benchmark.replay_verified else 0.05
    observed_run_count = max(
        execution_journal.total_runs,
        1 if benchmark.stage_count > 0 else 0,
    )
    observed_passing_runs = max(
        execution_journal.passing_runs,
        1 if benchmark.replay_verified else 0,
    )

    baseline_harmony = _clamp(
        average_live_score * 0.62
        + connector_reach * 0.12
        + replay_bonus
        + min(0.1, benchmark.stage_count / 80)
    )
    tension_index = _clamp(
        question_pressure * 0.52
        + min(1.0, warning_load / max(1, len(repository_pulse.lanes) * 3)) * 0.28
        + (0.0 if benchmark.replay_verified else 0.18)
    )

    bands = [
        CymaticBand(
            band_id="coverage",
            label="coverage breadth",
            intensity=_clamp(repository_pulse.route_count / 80),
            drift=_clamp(question_pressure * 0.48),
            note=(
                "Routes and connector kinds show how much ground the current "
                "runtime can actually hold."
            ),
        ),
        CymaticBand(
            band_id="repeatability",
            label="repeatable replay",
            intensity=1.0 if benchmark.replay_verified else 0.58,
            drift=0.08 if benchmark.replay_verified else 0.42,
            note=(
                "Replay parity matters because a strong claim is easier to "
                "revisit than to defend from memory."
            ),
        ),
        CymaticBand(
            band_id="review",
            label="review pressure",
            intensity=_clamp(1.0 - tension_index * 0.78),
            drift=_clamp(tension_index),
            note=(
                "Open questions and warnings are treated as part of the "
                "operating picture rather than hidden beneath a score."
            ),
        ),
        CymaticBand(
            band_id="movement",
            label="active movement",
            intensity=_clamp(min(1.0, observed_run_count / 18)),
            drift=_clamp(
                max(
                    0.0,
                    1.0
                    - observed_passing_runs / max(1, observed_run_count),
                )
            ),
            note=(
                "The engine feels more alive when scripts, exports, and "
                "verification runs continue to leave visible traces."
            ),
        ),
    ]

    stages = [
        _build_stage_card(
            stage=_find_stage(benchmark, "connector_ingest"),
            label="Ingest and shape",
            files=[
                "src/advanced_multimodal_ai/connectors.py",
                "src/advanced_multimodal_ai/catalog.py",
                "src/advanced_multimodal_ai/pipelines.py",
            ],
            trace_paths=[
                "/v1/connectors/register",
                "/v1/connectors/pipeline-ingest",
                "/v1/catalog/register",
            ],
            human_read=(
                "Different file shapes are named and typed before they turn into "
                "a convincing multimodal story."
            ),
            research_read=(
                "The intake lane keeps data cleaning observable, which makes later "
                "claims easier to revisit."
            ),
            business_read=(
                "Earlier shape checks mean fewer downstream reruns and less quiet "
                "damage from a broken source file."
            ),
            improvement_path=(
                "Keep widening connector evidence with more object-store and "
                "public-web reference sets."
            ),
            extra_metrics=[
                CymaticMetric(
                    metric_id="connector_kinds",
                    label="connector kinds",
                    value=research_bundle.summary.connector_kind_count,
                    unit="lanes",
                    detail="Typed intake paths currently exercised in the repository.",
                ),
            ],
        ),
        _build_stage_card(
            stage=_find_stage(benchmark, "profile_lane"),
            label="Profile and align",
            files=[
                "src/advanced_multimodal_ai/quality.py",
                "src/advanced_multimodal_ai/signal_math.py",
                "src/advanced_multimodal_ai/alignment.py",
            ],
            trace_paths=[
                "/v1/data/profile",
                "/v1/alignment/windows",
            ],
            human_read=(
                "Thin evidence is easier to notice when entropy, coverage, and timing are "
                "measured before fusion."
            ),
            research_read=(
                "This is the calmest place to study where a modality starts losing shape "
                "without blaming the model too early."
            ),
            business_read=(
                "Weak alignment usually means slower review, shakier output, and more manual "
                "correction later."
            ),
            improvement_path=(
                "Add more paired transcript, frame, and audio corpora so timing pressure can "
                "be studied under noisier conditions."
            ),
        ),
        _build_stage_card(
            stage=_find_stage(benchmark, "pipeline_replay"),
            label="Replay and prove",
            files=[
                "src/advanced_multimodal_ai/replay.py",
                "src/advanced_multimodal_ai/provenance.py",
                "src/advanced_multimodal_ai/pipeline_store.py",
            ],
            trace_paths=[
                "/v1/pipelines/runs/{run_id}/export",
                "/v1/pipelines/runs/{run_id}/replay",
            ],
            human_read=(
                "If a run can be replayed cleanly, the repository is giving you memory rather "
                "than theatre."
            ),
            research_read=(
                "Frame parity keeps sequence work honest. You can reopen the run instead of "
                "retelling it."
            ),
            business_read=(
                "Repeatable replay shortens incident review and makes procurement questions "
                "less expensive to answer."
            ),
            improvement_path=(
                "Keep replay evidence attached to more connector and batch routes so the proof "
                "surface deepens with use."
            ),
        ),
        _build_stage_card(
            stage=_find_stage(benchmark, "batch_job"),
            label="Concurrent batch work",
            files=[
                "src/advanced_multimodal_ai/job_store.py",
                "src/advanced_multimodal_ai/service.py",
                "src/advanced_multimodal_ai/api.py",
            ],
            trace_paths=[
                "/v1/jobs/batch-infer",
                "/v1/jobs",
            ],
            human_read=(
                "Longer work belongs in a job lane with visible status, not in a tab that "
                "looks busy and then forgets everything."
            ),
            research_read=(
                "The async lane shows how far the runtime has moved from toy request-response "
                "patterns without pretending to be a giant cluster."
            ),
            business_read=(
                "Clear job records make larger workloads easier to queue, inspect, and reopen "
                "when a customer asks what happened."
            ),
            improvement_path=(
                "The next careful step is a stronger distributed backplane, not more hidden "
                "work inside one process."
            ),
        ),
        _build_stage_card(
            stage=_find_stage(benchmark, "proof_bundle"),
            label="Govern and disclose",
            files=[
                "src/advanced_multimodal_ai/proof.py",
                "src/advanced_multimodal_ai/repository_pulse.py",
                "src/advanced_multimodal_ai/governance_ledger.py",
            ],
            trace_paths=[
                "/v1/proof/bundle",
                "/v1/repository/pulse",
                "/v1/runtime/compliance-ledger",
            ],
            human_read=(
                "The public pages stay calmer because the evidence is generated in the backend "
                "first and only translated afterward."
            ),
            research_read=(
                "Proof and posture now move with the code, which makes criticism easier to "
                "meet without overexplaining."
            ),
            business_read=(
                "A smaller, verifiable disclosure surface is easier to trust than a larger one "
                "that cannot point back to its own receipts."
            ),
            improvement_path=(
                "Keep adding thin, testable proof surfaces instead of piling more claims into "
                "the presentation layer."
            ),
            extra_metrics=[
                CymaticMetric(
                    metric_id="open_questions",
                    label="open questions",
                    value=research_bundle.summary.open_question_count,
                    unit="questions",
                    detail="Questions still kept visible in the research surface bundle.",
                ),
            ],
        ),
    ]

    lead_model = research_bundle.model_cards[0] if research_bundle.model_cards else None
    lead_finding = research_bundle.findings[0] if research_bundle.findings else None
    lead_connection = research_bundle.connections[0] if research_bundle.connections else None

    narratives = [
        CymaticNarrative(
            narrative_id="creator_lane",
            title="For creators and editors",
            audience="creator",
            summary=(
                "When the intake or profile lane begins to roughen, the output usually stops "
                "sounding like a nuanced audience and starts sounding like a narrow loop."
            ),
            consequence=(
                "The cost is not only technical. Repetition flattens taste, reduces surprise, "
                "and makes a catalogue feel smaller than it is."
            ),
            continuation=(
                lead_finding.summary if lead_finding else
                "The field notes keep the current findings in a smaller, more legible register."
            ),
        ),
        CymaticNarrative(
            narrative_id="operator_lane",
            title="For operators and review teams",
            audience="operator",
            summary=(
                "Replay parity, proof exports, and job records make it easier to answer what "
                "moved, what failed, and what deserves another pass."
            ),
            consequence=(
                "That shortens the distance between an incident, a rerun, and a clear decision "
                "about whether the lane can keep moving."
            ),
            continuation=(
                lead_connection.learning_value
                if lead_connection
                else (
                    "The connected file lanes show which modules begin, "
                    "carry, and close the runtime story."
                )
            ),
        ),
        CymaticNarrative(
            narrative_id="research_lane",
            title="For researchers and model builders",
            audience="researcher",
            summary=(
                lead_model.why_used
                if lead_model
                else (
                    "The research archive stays visible without pretending "
                    "every model in it is ready for the live edge."
                )
            ),
            consequence=(
                "That makes the repo more useful as a place to compare "
                "mechanisms, not only outputs."
            ),
            continuation=(
                lead_model.improvement_paths[0] if lead_model and lead_model.improvement_paths else
                "The model observatory keeps the next serious improvement paths visible."
            ),
        ),
    ]

    return CymaticSurfaceBundle(
        service=research_bundle.service,
        version=research_bundle.version,
        readiness_posture=research_bundle.readiness_posture,
        route_count=research_bundle.summary.route_count,
        test_count=research_bundle.summary.test_count,
        connector_kind_count=research_bundle.summary.connector_kind_count,
        replay_verified=benchmark.replay_verified,
        baseline_harmony=baseline_harmony,
        tension_index=tension_index,
        active_files=sum(len(lane.files) for lane in repository_pulse.lanes),
        total_runs=observed_run_count,
        harmonic_bands=bands,
        stages=stages,
        narratives=narratives,
        continuation_links=[
            "advanced-technical-portfolio.html",
            "benchmark-observatory.html",
            "model-observatory.html",
            "field-notes.html",
            "proof/cymatic-surface.md",
        ],
    )


def _build_stage_card(
    *,
    stage: BenchmarkStageResult | None,
    label: str,
    files: list[str],
    trace_paths: list[str],
    human_read: str,
    research_read: str,
    business_read: str,
    improvement_path: str,
    extra_metrics: list[CymaticMetric] | None = None,
) -> CymaticStageCard:
    stage_status = 1.0 if stage and stage.status == "pass" else 0.58
    duration_ratio = min(1.0, (stage.duration_ms if stage else 0.0) / 500)
    record_ratio = min(1.0, (stage.record_count if stage else 0) / 12)
    harmony_score = _clamp(stage_status * 0.62 + record_ratio * 0.18 + (1.0 - duration_ratio) * 0.2)
    friction_score = _clamp((1.0 - harmony_score) * 0.74 + duration_ratio * 0.16)

    metrics = [
        CymaticMetric(
            metric_id="duration",
            label="duration",
            value=round(stage.duration_ms if stage else 0.0, 2),
            unit="ms",
            detail="Recorded stage duration from the current reference workload.",
        ),
        CymaticMetric(
            metric_id="records",
            label="records",
            value=float(stage.record_count if stage else 0),
            unit="records",
            detail="Records or artifacts this stage reported while the reference workload ran.",
        ),
        CymaticMetric(
            metric_id="artifacts",
            label="artifacts",
            value=float(len(stage.artifacts) if stage else 0),
            unit="items",
            detail="Artifacts or identifiers kept visible for this stage.",
        ),
    ]
    if extra_metrics:
        metrics.extend(extra_metrics)

    return CymaticStageCard(
        stage_id=stage.stage_id if stage else label.lower().replace(" ", "_"),
        label=label,
        harmony_score=harmony_score,
        friction_score=friction_score,
        trace_paths=trace_paths,
        files=files,
        human_read=human_read,
        research_read=research_read,
        business_read=business_read,
        improvement_path=improvement_path,
        metrics=metrics,
    )


def _find_stage(
    benchmark: ReferenceBenchmarkResult,
    stage_id: str,
) -> BenchmarkStageResult | None:
    for stage in benchmark.stages:
        if stage.stage_id == stage_id:
            return stage
    return None


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
