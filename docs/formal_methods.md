# Formal Methods

The industrial diagnostics lane uses formal structure in three places.

## 1. Symbolic threshold evaluation

The rule engine evaluates declared signal thresholds such as oil pressure, coolant
temperature, voltage imbalance, and contamination level. If `z3-solver` is installed,
each comparison is translated into a solver constraint before the rule is accepted.

## 2. State-machine discipline

The transition graph is intentionally narrow:

- `observe -> isolate`
- `isolate -> verify`
- `verify -> intervene | hold | restart`
- `intervene -> verify | hold | restart`
- `restart -> observe | hold`
- `hold -> observe | isolate`

Any transition outside that graph is rejected by the model-checking lane.

## 3. Invariant checks

Three invariants stay visible in the response:

- lockout before intervention
- protective controls before restart
- critical faults do not route

The proofs are modest, but they are executable and test-covered. That matters more here than
grander claims with no runtime boundary.
