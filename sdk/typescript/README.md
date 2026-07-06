# Advanced Multi-modal AI TypeScript SDK

This package includes the hand-kept client surface in `src/index.ts` together
with generated OpenAPI-derived methods in `src/generated-openapi.ts`.

The hand-kept client validates tensor requests before sending them. It checks
shape length, positive integer dimensions, flattened value counts, and
non-finite values. Use `validateInferenceRequest()` when you want a report, or
let `AdvancedMultimodalAIClient` call `assertInferenceRequest()` before
profile, provenance, plan, infer, and stream requests.

Refresh the generated client from the repository root:

```bash
python3 scripts/export_openapi.py
python3 scripts/generate_sdk_surfaces.py
```
