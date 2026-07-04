# Regulatory Compliance

This repository does not claim to be a complete legal implementation of OSHA, ISO, or IEC
standards. It does something narrower and more defensible: it turns a few high-value safety
obligations into deterministic checks that can travel with a diagnostic request.

## OSHA 1910

The active lane watches lockout and hazardous-energy isolation before direct intervention.
If the machine is headed toward hands-on work without both controls, the result is blocked.

## ISO 13849

The lane checks whether protective guards, emergency stop posture, and manual reset
verification are ready before a restart path is treated as valid.

## IEC 61508

The lane checks whether overdue proof testing and weak diagnostic coverage are being ignored
while a severe machine fault is already present.

The point is not to mimic a full compliance manual inside the code. The point is to stop the
most brittle operational shortcuts from disappearing into a probabilistic answer.
