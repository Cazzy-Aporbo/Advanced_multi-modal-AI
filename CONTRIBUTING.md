# Contributing

The repository is easiest to extend when every change stays tied to one real lane:
an API surface, a proof export, a public study page, a compiled primitive, or a
domain transfer question that can be verified.

## Before you open a pull request

1. Keep the scope narrow enough to explain in a few sentences.
2. Prefer executable files over notebooks or presentation-only assets.
3. If a new surface makes a claim, add the route, test, or export that proves it.
4. If a route changes shape, regenerate the OpenAPI and SDK surfaces.
5. If a public page changes, make sure it still reads generated proof instead of
   inventing its own story.

## Local verification

Run the checks that match the lane you touched:

```bash
python3 -m pytest -q
python3 -m ruff check src tests scripts
cargo test -p multimodal-core
python3 scripts/run_acceptance_spine.py
python3 scripts/export_openapi.py
python3 scripts/generate_sdk_surfaces.py
```

If you changed public proof or observatory pages, also refresh the export files:

```bash
python3 scripts/export_research_surfaces.py
python3 scripts/export_repository_pulse.py
python3 scripts/export_repository_growth.py
python3 scripts/export_music_observatory.py
python3 scripts/export_industry_profiles.py
```

## Change style

- Keep variable names explicit.
- Prefer typed contracts to loose dictionaries.
- Keep frontend language calm and precise.
- Avoid synthetic traffic, decorative benchmark claims, or placeholder telemetry.
- Keep raw media out of the repository; prefer manifests, receipts, and derived features.

## Good contributions

- A route that becomes easier to verify
- A proof export that becomes easier to diff
- A domain profile that maps more closely to the live API
- A music or multimodal lane that surfaces a real blind spot
- A public page that becomes clearer without becoming louder

## Pull request shape

The strongest pull requests usually include:

- one short reason for the change
- the files or lanes affected
- the exact commands run locally
- one note on what still remains outside the current scope
