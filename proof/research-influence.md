# Research Influence Proof

- Sources: `4`
- Mechanisms: `6`
- Feature surfaces: `6`
- Routes: `106`
- Tests: `64`

## Sources

- **Self-Harness: Harnesses That Improve Themselves** (2026) - weakness mining from execution traces; minimal harness proposal; regression-gated promotion
- **Investigating Multi-Agent Deliberation in Law** (2026) - multi-agent deliberation; 3-ply adversarial argument; role-diverse critique
- **AI, Trust, and the War Room: Evidence from a Conjoint Experiment** (2026) - trust calibration; human control; oversight sensitivity; mission and harm tradeoff
- **AI Epistemic Risks: Emerging Mechanisms and Evidence** (2026) - persuasion and manipulation; cognitive offloading; feedback loops and lock-in; epistemic diversity

## Mechanisms now represented in code

- **Weakness mining from traces** - `active` - score `86` - routes: /v1/execution/journal, /v1/growth/snapshot, /v1/research/harness-improvement
- **Regression-gated change promotion** - `active` - score `84` - routes: /v1/proof/bundle, /v1/readiness/report
- **Deliberative disagreement matrix** - `active` - score `77` - routes: /v1/industries/profiles, /v1/bias/assess, /v1/research/deliberation/assess
- **Trust calibration with oversight** - `active` - score `87` - routes: /v1/readiness/report, /v1/edge/evaluate, /v1/industrial/diagnose, /v1/research/trust/calibrate
- **Epistemic friction against over-delegation** - `active` - score `82` - routes: /v1/music/drift, /v1/research/surfaces, /v1/operators/surfaces, /v1/research/epistemic-risk/assess
- **Feedback-loop and lock-in monitoring** - `partial` - score `69` - routes: /v1/music/drift, /v1/drift/check, /v1/repository/pulse

## Harness improvement sample

- Failed traces: `3`
- Promoted proposals: `1`

- **proposal:acceptance-spine:stale-proof** - `promote` - The next run should keep the successful traces stable while forcing this repeated weakness to appear as a testable failure if it returns.
- **proposal:acceptance-spine:schema-drift** - `hold` - The next run should keep the successful traces stable while forcing this repeated weakness to appear as a testable failure if it returns.

## Deliberation sample

- Recommendation: `escalate`
- Disagreement score: `0.6667`
- Missing roles: `reviewer`

## Trust calibration sample

- Band: `medium`
- Review required: `True`
- Score: `0.6178`

## Epistemic risk sample

- Band: `low`
- Score: `0.205`

- **Evidence diversity** - score `0.0` - 3 perspectives and 4 source types appear across 4 items.
- **Unsupported certainty** - score `0.5` - 2 high-confidence items hide uncertainty.
- **Repetition pressure** - score `0.25` - 1 repeated claims were found after normalization.
- **Human review gap** - score `0.0` - 1 evidence items were marked as human-generated.
- **Freshness** - score `0.25` - 1 evidence items are older than 180 days.
