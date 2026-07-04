# Industrial Diagnostics Bundle

- Sample asset kind: `diesel_engine`
- Machine family: `field-diagnostics-reference`
- Verdict: `block`
- Diagnoses: `2`
- Compliance findings: `3`
- Proof nodes: `11`
- Audit entries: `5`

## Scenarios

- `diesel-engine-overheat-window` · `diesel_engine` · Diesel engine overheat window · expected diesel-lubrication-collapse, diesel-airpath-restriction
- `hydraulic-cavitation-and-debris` · `hydraulic_system` · Hydraulic cavitation and debris · expected hydraulic-cavitation-window, hydraulic-contamination-escalation
- `electrical-phase-loss` · `electrical_system` · Electrical phase loss and insulation drift · expected electrical-phase-loss, electrical-insulation-breakdown

## Sample diagnoses

- `diesel-lubrication-collapse` · critical · Lubrication collapse risk · confidence 0.99
- `diesel-airpath-restriction` · high · Air-path restriction or boost collapse · confidence 0.99

## Compliance findings

- `OSHA 1910 1910.147` · block · Lockout and energy isolation must be established before direct intervention.
- `ISO 13849-1 5.2.2` · watch · A deliberate reset confirmation is required after the safeguarded stop.
- `IEC 61508 7.4.9` · block · Overdue proof testing and weak diagnostic coverage must be cleared before safety claims are reused.

## Invariants

- `lockout-before-intervention` · holds=False
- `restart-after-protective-controls` · holds=False
- `critical-faults-do-not-route` · holds=False
