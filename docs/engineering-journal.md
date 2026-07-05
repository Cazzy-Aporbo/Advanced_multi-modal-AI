# Engineering Journal

This repository treats progress as something that should be inspectable later.
When a lane changes, the useful record is not only what passed. It is also what
failed, what was narrowed, and what evidence was left behind.

## Working Standard

| Habit | What gets recorded | Where it shows up |
| --- | --- | --- |
| Run the smallest proof first | focused test, route, or export command | pull request notes, execution journal, proof export |
| Keep failed attempts useful | command, error shape, suspected cause, next correction | pull request notes or issue comment |
| Regenerate what the page reads | JSON and Markdown proof artifacts | `proof/*.json`, `proof/*.md` |
| Tie public pages to generated data | route, proof file, or static export | HTML surfaces and `research-surfaces.js` loaders |
| Separate claim from capability | what is active, exploratory, generated, or missing | README lane tables, file atlas, runtime pulse |

## Pass And Fail Record

Use this shape when a change is non-trivial.

```text
Lane:
Changed:
Command:
Result: pass | fail | blocked
Evidence:
What changed after the result:
What still needs review:
```

Short records are better than vague confidence. A failed test that changed the
design is still useful evidence.

## Reference Implementation Criteria

A feature is ready to be treated as part of the reference path when it has:

| Requirement | Minimum evidence |
| --- | --- |
| Contract | Pydantic model, OpenAPI route, or typed CLI input |
| Runtime path | function or service method used by a route, script, or test |
| Proof path | generated artifact, execution journal entry, or reproducible command |
| Public reading path | page, README section, or Markdown proof file that reads generated data |
| Failure shape | test, validator, or documented blocked case |

## Current Learning Loop

| Surface | What it now proves | Next pressure to keep honest |
| --- | --- | --- |
| Runtime proof | routes, tests, commands, artifacts, stores | keep command list aligned with every new export |
| Repository pulse | lane health and artifact presence | avoid hiding weak lanes behind aggregate scores |
| Repository file map | file purpose, inputs, outputs, connections | keep static analysis conservative and auditable |
| Benchmark surface | reference workload and replay memory | add more realistic large-shape fixtures without storing private data |
| Music warehouse | manifests, derived features, drift | keep raw media outside the repo while expanding feature proof |
| Privacy membrane | local deterministic masking receipts | keep taxonomy honest about what is rule-based, not trained |

## Issue And Pull Request Discipline

If a reviewer cannot tell what changed, what proof moved, and what remains
unfinished, the contribution is not yet shaped well enough. Keep the work modest
enough to examine and precise enough to rerun.
