from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from advanced_multimodal_ai.contracts import RecipeRecord

    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 scripts/validate_recipe_manifest.py <manifest.json>")
    manifest_path = Path(sys.argv[1])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = RecipeRecord.model_validate(payload)
    print(
        json.dumps(
            {
                "recipe_id": record.recipe_id,
                "label": record.label,
                "objective": record.objective,
                "launcher": record.launch_profile.launcher if record.launch_profile else "",
                "verified_command_count": len(record.launch_profile.verified_commands)
                if record.launch_profile
                else 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
