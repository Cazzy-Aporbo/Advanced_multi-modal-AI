# Security

If you find a vulnerability, please avoid opening a public issue with exploit
details before the repository owner has had a chance to assess it.

## What to include

- the affected route, file, or public surface
- a short description of the impact
- steps to reproduce
- whether the issue requires local access, a crafted payload, or a specific deployment setting
- any logs, request shapes, or proof artifacts that make the issue easier to verify

## Preferred report path

Send a private report to the repository owner through the contact method listed
on the GitHub profile or via a private security advisory if that feature is enabled.

## Response posture

- confirm receipt
- reproduce the issue
- decide whether the fix belongs in the runtime, compiled core, proof export, or public surface
- patch, verify, and document the change

## Supported focus

The highest-priority reports are:

- schema drift and contract bypass
- provenance or proof corruption
- unsafe connector behavior
- retrieval boundary failures
- route-level leakage across public surfaces
- mistakes in derived audio or multimodal warehouse handling
