from __future__ import annotations

from .contracts import IndustryProfile, IndustryProfileBundle


def build_industry_profile_bundle() -> IndustryProfileBundle:
    profiles = [
        IndustryProfile(
            profile_id="healthcare",
            label="Healthcare",
            primary_modalities=["text", "tabular", "audio", "image"],
            why_multimodal_matters=(
                "Clinical notes, structured measurements, dictation, and imaging "
                "rarely agree on their own. The runtime has to preserve the evidence "
                "path between them before anyone treats a correlation as a finding."
            ),
            anchor_routes=[
                "/v1/catalog/register",
                "/v1/drift/check",
                "/v1/ontology/liability",
                "/v1/data/provenance",
            ],
            strict_checks=[
                "schema fingerprinting before downstream reuse",
                "population-entry drift before cohort transfer",
                "provenance receipts for repeated chart review",
            ],
            supply_chain_focus=(
                "Watch how annotations, clinical exports, and downstream feature "
                "tables inherit the same residency and retention rules."
            ),
            signal_questions=[
                "Did the measured population shift before the model changed?",
                "Which record stayed closest to the final decision path?",
            ],
            proof_surfaces=[
                "proof/runtime-proof.json",
                "proof/research-surfaces.json",
            ],
        ),
        IndustryProfile(
            profile_id="employment",
            label="Employment",
            primary_modalities=["text", "audio", "tabular"],
            why_multimodal_matters=(
                "Hiring and performance systems combine resumes, interview signals, "
                "scores, and workflow metadata. The fragile part is not the scoring "
                "formula alone but the path that introduced imbalance upstream."
            ),
            anchor_routes=[
                "/v1/catalog/evolution",
                "/v1/bias/assess",
                "/v1/drift/check",
                "/v1/edge/evaluate",
            ],
            strict_checks=[
                "stage-aware bias review",
                "dataset evolution checks before ranking logic moves",
                "edge routing review for cross-border applicant data",
            ],
            supply_chain_focus=(
                "Keep interview transcripts, score tables, and exported decisions tied "
                "to the same change-control record."
            ),
            signal_questions=[
                "Where did representational narrowing enter the process?",
                "Which review lane can still interrupt a bad automation path?",
            ],
            proof_surfaces=[
                "proof/operator-surfaces.json",
                "proof/edge-topology.json",
            ],
        ),
        IndustryProfile(
            profile_id="education",
            label="Education",
            primary_modalities=["text", "audio", "image"],
            why_multimodal_matters=(
                "Assignments, lecture capture, annotations, and classroom support "
                "signals need to stay legible for learners, not just for evaluation."
            ),
            anchor_routes=[
                "/v1/video/packet",
                "/v1/video/clean",
                "/v1/alignment/windows",
                "/v1/drift/check",
            ],
            strict_checks=[
                "transcript-first video packetization",
                "alignment windows before lesson claims are summarized",
                "drift baselines for language and access patterns",
            ],
            supply_chain_focus=(
                "Keep the handoff from lecture capture to cleaned teaching asset "
                "visible enough for a teacher to question it."
            ),
            signal_questions=[
                "Did cleanup remove context instead of noise?",
                "Which modality stayed behind when comprehension dropped?",
            ],
            proof_surfaces=[
                "proof/benchmark-surfaces.json",
                "proof/cymatic-surface.json",
            ],
        ),
        IndustryProfile(
            profile_id="business_operations",
            label="Business operations",
            primary_modalities=["text", "tabular", "image"],
            why_multimodal_matters=(
                "Operational systems mix invoices, contracts, screenshots, logs, and "
                "metrics. The useful question is where the evidence chain thinned out, "
                "not how quickly a dashboard rendered."
            ),
            anchor_routes=[
                "/v1/ontology/ingest",
                "/v1/ontology/liability",
                "/v1/recipes/compile",
                "/v1/jobs/batch-infer",
            ],
            strict_checks=[
                "ontology snapshots tied to workflow claims",
                "liability surfacing before orchestration expands",
                "batch receipts with persisted run records",
            ],
            supply_chain_focus=(
                "Keep contracts, workflow rules, and exported decisions readable as "
                "one chain instead of three adjacent systems."
            ),
            signal_questions=[
                "Which rule lives in code, and which one still lives in memory?",
                "Can the batch lane be replayed without improvising missing context?",
            ],
            proof_surfaces=[
                "proof/example-bundle.json",
                "proof/repository-pulse.json",
            ],
        ),
        IndustryProfile(
            profile_id="sports",
            label="Sports",
            primary_modalities=["video", "audio", "tabular", "text"],
            why_multimodal_matters=(
                "Tracking feeds, commentary, sensor rows, and clipping windows need "
                "temporal alignment before a coaching or officiating story becomes "
                "credible."
            ),
            anchor_routes=[
                "/v1/video/packet",
                "/v1/alignment/windows",
                "/v1/pipelines/runs/{run_id}/export",
                "/v1/data/provenance",
            ],
            strict_checks=[
                "temporal alignment around event windows",
                "replay parity before highlight or review claims",
                "provenance receipts for contested moments",
            ],
            supply_chain_focus=(
                "Preserve which camera, commentary slice, and metric feed shaped a "
                "single segment-level judgment."
            ),
            signal_questions=[
                "Which modality disagreed first when the sequence changed?",
                "Can a disputed replay be reconstructed from stored evidence alone?",
            ],
            proof_surfaces=[
                "proof/benchmark-surfaces.json",
                "proof/execution-journal.json",
            ],
        ),
        IndustryProfile(
            profile_id="media",
            label="Media",
            primary_modalities=["audio", "text", "video", "image"],
            why_multimodal_matters=(
                "Catalog behavior is shaped by sound, visuals, metadata, and copy at "
                "once. The repository is strongest when it can show where repetition, "
                "silence, and homogenization started to compound."
            ),
            anchor_routes=[
                "/v1/music/features/extract",
                "/v1/music/drift",
                "/v1/music/proof/change-report",
                "/v1/benchmarks/reference",
            ],
            strict_checks=[
                "manifest-only audio intake",
                "segment index plus derived feature warehouse",
                "language-share and loudness drift monitoring",
            ],
            supply_chain_focus=(
                "Keep track references, feature runs, embeddings, and drift receipts "
                "closer than the public story built on them."
            ),
            signal_questions=[
                "Is repetition entering through production polish rather than taste?",
                "Which catalog shift is visible before the ranking layer notices it?",
            ],
            proof_surfaces=[
                "proof/music-observatory.json",
                "proof/cymatic-surface.json",
            ],
        ),
        IndustryProfile(
            profile_id="journalism",
            label="Journalism",
            primary_modalities=["text", "audio", "image", "video"],
            why_multimodal_matters=(
                "Interview audio, source documents, screenshots, and reporting notes "
                "must stay attributable enough that a correction can reach the exact "
                "moment where the story bent."
            ),
            anchor_routes=[
                "/v1/data/provenance",
                "/v1/edge/evaluate",
                "/v1/video/clean",
                "/v1/ontology/liability",
            ],
            strict_checks=[
                "receipt issuance for repeated claims",
                "edge evaluation before cross-border publication lanes",
                "cleanup planning that preserves attribution",
            ],
            supply_chain_focus=(
                "Treat source movement, transcript cleanup, and downstream publication "
                "as one auditable chain."
            ),
            signal_questions=[
                "Which asset can still defend the claim if a quote is challenged?",
                "Did cleanup preserve meaning or only remove friction?",
            ],
            proof_surfaces=[
                "proof/edge-topology.json",
                "proof/example-bundle.json",
            ],
        ),
        IndustryProfile(
            profile_id="dentistry",
            label="Dentistry",
            primary_modalities=["image", "text", "tabular"],
            why_multimodal_matters=(
                "Imaging, treatment notes, and structured chart data need the same "
                "record of what changed between intake, review, and follow-up."
            ),
            anchor_routes=[
                "/v1/catalog/register",
                "/v1/data/provenance",
                "/v1/drift/check",
                "/v1/edge/evaluate",
            ],
            strict_checks=[
                "contract registration before image-derived fields expand",
                "population drift checks for narrow cohorts",
                "edge review before external routing",
            ],
            supply_chain_focus=(
                "Keep imaging derivatives, care-plan notes, and exported follow-up "
                "artifacts under one review rhythm."
            ),
            signal_questions=[
                "Did the image-derived feature move farther than the chart note?",
                "Which cohort assumption became too narrow to reuse safely?",
            ],
            proof_surfaces=[
                "proof/runtime-proof.json",
                "proof/edge-topology.json",
            ],
        ),
        IndustryProfile(
            profile_id="biology",
            label="Biology",
            primary_modalities=["tabular", "image", "text"],
            why_multimodal_matters=(
                "Microscopic imagery, assay tables, and lab notes reward small "
                "differences only when the pipeline preserves scale, timing, and "
                "field meaning together."
            ),
            anchor_routes=[
                "/v1/catalog/register",
                "/v1/data/profile",
                "/v1/alignment/windows",
                "/v1/data/provenance",
            ],
            strict_checks=[
                "field-level dataset registration",
                "quality profiling before fusion",
                "alignment windows for paired assay and image slices",
            ],
            supply_chain_focus=(
                "Watch how specimen metadata, measurement tables, and image windows "
                "separate or stay coupled through export."
            ),
            signal_questions=[
                "Which finite detail disappeared when the table was cleaned?",
                "Can the microscopy slice still be traced from result back to source?",
            ],
            proof_surfaces=[
                "proof/research-surfaces.json",
                "proof/runtime-proof.json",
            ],
        ),
        IndustryProfile(
            profile_id="industrial_diagnostics",
            label="Industrial diagnostics",
            primary_modalities=["text", "tabular", "audio", "image"],
            why_multimodal_matters=(
                "Field troubleshooting tends to compress machine state into one fast "
                "story. The stronger pattern is to keep technician language, sensor "
                "evidence, compliance posture, and restart logic visible at once."
            ),
            anchor_routes=[
                "/v1/industrial/scenarios",
                "/v1/industrial/diagnose",
                "/v1/industrial/model-check",
                "/v1/edge/evaluate",
            ],
            strict_checks=[
                "formal trace checks before restart",
                "lockout and guard verification before intervention",
                "proof-tree and audit-chain generation for each diagnostic pass",
            ],
            supply_chain_focus=(
                "Keep machine symptoms, sensor drift, safety obligations, and final "
                "maintenance posture sealed into one diagnostic chain."
            ),
            signal_questions=[
                "Which fault path became visible before the field team touched the machine?",
                "Can restart logic still be defended if the trace is replayed later?",
            ],
            proof_surfaces=[
                "proof/industrial-diagnostics.json",
                "proof/edge-topology.json",
            ],
        ),
        IndustryProfile(
            profile_id="construction",
            label="Construction",
            primary_modalities=["image", "video", "tabular", "text"],
            why_multimodal_matters=(
                "Field imagery, project logs, schedules, and procurement records move "
                "on different clocks. The system has to keep their time relationship "
                "intact before someone declares a risk or delay."
            ),
            anchor_routes=[
                "/v1/stewardship/supply-chain",
                "/v1/recipes/compile",
                "/v1/video/packet",
                "/v1/pipelines/runs/{run_id}/export",
            ],
            strict_checks=[
                "supply-chain edge review",
                "recipe compilation with proof obligations",
                "video windowing around site events",
            ],
            supply_chain_focus=(
                "Track how vendor files, site imagery, and schedule deltas enter the "
                "same operational account."
            ),
            signal_questions=[
                "Which downstream delay came from missing evidence rather than late work?",
                "Can a site event be replayed with the same context later?",
            ],
            proof_surfaces=[
                "proof/repository-pulse.json",
                "proof/benchmark-surfaces.json",
            ],
        ),
        IndustryProfile(
            profile_id="supply_chain",
            label="Supply chain",
            primary_modalities=["tabular", "text", "image"],
            why_multimodal_matters=(
                "Purchase records, scanned paperwork, issue notes, and vendor images "
                "create liability when they drift apart faster than reviewers can see."
            ),
            anchor_routes=[
                "/v1/stewardship/supply-chain",
                "/v1/stewardship/change-controls",
                "/v1/ontology/liability",
                "/v1/edge/evaluate",
            ],
            strict_checks=[
                "governed edge mapping",
                "change-control records before route shifts",
                "liability surfacing against stated obligations",
            ],
            supply_chain_focus=(
                "Keep source nodes, destination nodes, deletion posture, and "
                "cross-border edges visible in the same record."
            ),
            signal_questions=[
                "Which ungoverned edge still carries business-critical data?",
                "Did the route expand before the control surface changed with it?",
            ],
            proof_surfaces=[
                "proof/runtime-proof.json",
                "proof/edge-topology.json",
            ],
        ),
    ]

    return IndustryProfileBundle(
        profile_count=len(profiles),
        continuation_links=[
            "advanced-technical-portfolio.html",
            "technical-portfolio.html",
            "model-observatory.html",
            "industrial-diagnostics.html",
            "music-observatory.html",
            "proof/industry-profiles.md",
        ],
        profiles=profiles,
    )
