# Industrial Diagnostics Architecture

This lane keeps three concerns in the same executable surface:

1. Sensor and observation evidence.
2. Safety and compliance constraints.
3. Restart and intervention state transitions.

The reasoner stays deterministic. Rules are declared in
`src/advanced_multimodal_ai/industrial_diagnostics/deterministic_engine/symbolic_reasoner.py`.
When `z3` is available, threshold comparisons are proven through solver-backed constraints.
When it is not, the same rule set still executes through explicit comparison operators, so the
diagnostic path remains reproducible.

The compliance layer does not sit beside the machine diagnosis as a narrative afterthought.
OSHA 1910 lockout expectations, ISO 13849 protective-control checks, and IEC 61508 proof-test
posture are evaluated in the same pass and folded into the final verdict.

Formal state transitions remain small on purpose:

- `observe`
- `isolate`
- `verify`
- `intervene`
- `restart`
- `hold`

The model-checking lane rejects trace shapes that attempt to restart too early or intervene
without lockout and energy isolation.
