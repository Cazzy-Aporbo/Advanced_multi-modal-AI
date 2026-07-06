from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PROOF_DIR = REPO_ROOT / "proof"
ASSET_DIR = REPO_ROOT / "assets" / "readme"


PALETTE = {
    "ink": "#16151a",
    "panel": "#201b24",
    "panel_2": "#172326",
    "rose": "#f0b7d3",
    "copper": "#f3b274",
    "jade": "#9adfd4",
    "blue": "#9bbcff",
    "lilac": "#c7b4ff",
    "cream": "#fff7ef",
    "muted": "#d8ccbf",
}


def load_json(name: str) -> dict[str, Any]:
    return json.loads((PROOF_DIR / name).read_text(encoding="utf-8"))


def write_svg(name: str, body: str, width: int, height: int, title: str) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-labelledby="title desc" viewBox="0 0 {width} {height}">'
        f"""
  <title id="title">{escape(title)}</title>
  <desc id="desc">Generated from repository proof files by scripts/export_readme_visuals.py.</desc>
  <defs>
    <linearGradient id="atlas" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="#1b1721"/>
      <stop offset="38%" stop-color="#26323a"/>
      <stop offset="72%" stop-color="#201826"/>
      <stop offset="100%" stop-color="#182927"/>
    </linearGradient>
    <linearGradient id="softLine" x1="0" x2="1">
      <stop offset="0%" stop-color="{PALETTE['copper']}"/>
      <stop offset="32%" stop-color="{PALETTE['rose']}"/>
      <stop offset="66%" stop-color="{PALETTE['jade']}"/>
      <stop offset="100%" stop-color="{PALETTE['blue']}"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="45%" r="60%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.42"/>
      <stop offset="45%" stop-color="{PALETTE['rose']}" stop-opacity="0.24"/>
      <stop offset="100%" stop-color="{PALETTE['jade']}" stop-opacity="0"/>
    </radialGradient>
    <filter id="blurGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="14"/>
    </filter>
  </defs>
  {body}
</svg>
"""
    )
    (ASSET_DIR / name).write_text(svg, encoding="utf-8")
    print(ASSET_DIR / name)


def text(
    x: int,
    y: int,
    value: str,
    size: int = 22,
    fill: str = "cream",
    weight: int = 500,
) -> str:
    color = PALETTE.get(fill, fill)
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-family="Georgia, serif" '
        f'font-size="{size}" font-weight="{weight}">{escape(value)}</text>'
    )


def label(x: int, y: int, value: str, size: int = 14, fill: str = "muted") -> str:
    color = PALETTE.get(fill, fill)
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-family="Avenir, Verdana, sans-serif" '
        f'font-size="{size}" letter-spacing="3">{escape(value.upper())}</text>'
    )


def fill_attributes(fill: str) -> str:
    if fill.startswith("rgba(255,255,255,") and fill.endswith(")"):
        opacity = fill.removeprefix("rgba(255,255,255,").removesuffix(")")
        return f'fill="#ffffff" fill-opacity="{opacity}"'
    return f'fill="{fill}"'


def rounded_rect(
    x: int,
    y: int,
    width: int,
    height: int,
    fill: str,
    stroke: str = "#ffffff22",
    radius: int = 24,
) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" '
        f'{fill_attributes(fill)} stroke="{stroke}" stroke-width="1.2"/>'
    )


def metric_card(x: int, y: int, label_value: str, number: str, color: str) -> str:
    return "\n".join(
        [
            rounded_rect(x, y, 150, 86, "rgba(255,255,255,0.055)", "#ffffff2c", 22),
            f'<rect x="{x}" y="{y}" width="150" height="3" rx="1.5" fill="{color}"/>',
            label(x + 18, y + 30, label_value, 12, "muted"),
            text(x + 18, y + 68, number, 30, "cream", 700),
        ]
    )


def rect(
    x: int,
    y: int,
    width: int,
    height: int,
    fill: str,
    radius: int = 0,
    opacity: float | None = None,
) -> str:
    opacity_attr = "" if opacity is None else f' opacity="{opacity}"'
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="{radius}" fill="{fill}"{opacity_attr}/>'
    )


def circle(
    x: int,
    y: int,
    radius: int,
    fill: str,
    opacity: float | None = None,
    extra: str = "",
) -> str:
    opacity_attr = "" if opacity is None else f' opacity="{opacity}"'
    return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}"{opacity_attr}>{extra}</circle>'


def animated_opacity(duration: int) -> str:
    return (
        '<animate attributeName="opacity" values="0.35;0.95;0.35" '
        f'dur="{duration}s" repeatCount="indefinite"/>'
    )


def export_signal_atlas() -> None:
    runtime = load_json("runtime-proof.json")
    file_map = load_json("repository-file-map.json")
    repo_pulse = load_json("repository-pulse.json")
    route_count = runtime.get("route_count", 0)
    test_count = runtime.get("test_count", 0)
    file_count = file_map.get("file_count", 0)
    edge_count = file_map.get("edge_count", 0)
    model_count = repo_pulse.get("model_count", 0)

    wave = []
    for index in range(0, 18):
        x = 610 + index * 26
        y = 210 + (index % 5 - 2) * 12
        radius = 4 + (index % 4)
        colors = [PALETTE["rose"], PALETTE["copper"], PALETTE["jade"], PALETTE["blue"]]
        wave.append(
            circle(
                x,
                y,
                radius,
                colors[index % len(colors)],
                0.82,
                animated_opacity(4 + index % 5),
            )
        )
    curve = (
        '<path d="M62 292 C232 202 314 328 470 242 '
        'S746 155 914 218 S1096 286 1140 174" fill="none" '
        'stroke="url(#softLine)" stroke-width="5" opacity="0.8"/>'
    )
    subtitle = (
        "Contracts, replay, alignment, music features, privacy receipts, "
        "and generated proof stay close to the code that creates them."
    )
    body = "\n".join(
        [
            '<rect width="1200" height="360" rx="34" fill="url(#atlas)"/>',
            (
                '<circle cx="1010" cy="72" r="160" fill="url(#glow)" '
                'filter="url(#blurGlow)" opacity="0.75"/>'
            ),
            (
                f'<circle cx="146" cy="286" r="120" fill="{PALETTE["rose"]}" '
                'opacity="0.10" filter="url(#blurGlow)"/>'
            ),
            curve,
            label(72, 78, "runtime atlas", 15, "copper"),
            text(72, 142, "Signals measured before output.", 48, "cream", 700),
            text(74, 186, subtitle, 19, "muted", 400),
            metric_card(72, 226, "routes", str(route_count), PALETTE["rose"]),
            metric_card(242, 226, "tests", str(test_count), PALETTE["jade"]),
            metric_card(412, 226, "files", str(file_count), PALETTE["blue"]),
            metric_card(582, 226, "edges", str(edge_count), PALETTE["copper"]),
            metric_card(752, 226, "models", str(model_count), PALETTE["lilac"]),
            "".join(wave),
        ]
    )
    write_svg("signal-atlas.svg", body, 1200, 360, "Advanced Multi-modal AI signal atlas")


def export_runtime_map() -> None:
    nodes = [
        ("Ingest", "typed connectors", 72, 120, PALETTE["copper"]),
        ("Contract", "schema fingerprint", 252, 120, PALETTE["rose"]),
        ("Profile", "quality receipt", 432, 120, PALETTE["jade"]),
        ("Align", "temporal window", 612, 120, PALETTE["blue"]),
        ("Replay", "ledger frame", 792, 120, PALETTE["lilac"]),
        ("Surface", "proof export", 972, 120, PALETTE["copper"]),
    ]
    parts = ['<rect width="1200" height="420" rx="34" fill="url(#atlas)"/>']
    parts.append(
        '<path d="M120 230 H1080" stroke="url(#softLine)" stroke-width="4" '
        'stroke-linecap="round" opacity="0.75"/>'
    )
    for index, (name, sub, x, y, color) in enumerate(nodes):
        if index < len(nodes) - 1:
            parts.append(
                f'<path d="M{x + 126} {y + 56} H{x + 168}" '
                f'stroke="{color}" stroke-width="3" opacity="0.65"/>'
            )
        parts.append(
            rounded_rect(x, y, 138, 118, "rgba(255,255,255,0.055)", color + "88", 26)
        )
        parts.append(circle(x + 69, y + 34, 12, color, 0.86))
        parts.append(text(x + 22, y + 70, name, 24, "cream", 700))
        parts.append(label(x + 22, y + 98, sub, 10, "muted"))
    lanes = [
        ("Python", "API, stores, proof, workers", PALETTE["blue"]),
        ("Rust", "tensor signatures, guard, replay, receipts", PALETTE["copper"]),
        ("TypeScript", "SDK validation and generated clients", PALETTE["jade"]),
        ("HTML/JS", "public reading surfaces from proof files", PALETTE["rose"]),
    ]
    x = 82
    for name, sub, color in lanes:
        parts.append(
            rounded_rect(x, 292, 245, 72, "rgba(255,255,255,0.05)", "#ffffff22", 22)
        )
        parts.append(
            f'<rect x="{x}" y="292" width="245" height="3" rx="1.5" fill="{color}"/>'
        )
        parts.append(text(x + 18, 324, name, 22, "cream", 700))
        parts.append(label(x + 18, 348, sub, 9, "muted"))
        x += 268
    parts.append(label(72, 72, "data path", 14, "copper"))
    parts.append(
        text(72, 98, "One request, several languages, one receipt trail.", 28, "cream", 700)
    )
    write_svg("runtime-map.svg", "\n".join(parts), 1200, 420, "Runtime map")


def export_proof_bars() -> None:
    file_map = load_json("repository-file-map.json")
    benchmark = load_json("benchmark-surfaces.json")
    languages = file_map.get("language_counts", {})
    max_count = max(languages.values()) if languages else 1
    parts = ['<rect width="1200" height="420" rx="34" fill="url(#atlas)"/>']
    parts.append(label(72, 72, "proof metrics", 14, "copper"))
    parts.append(text(72, 104, "The repository has a measurable shape.", 30, "cream", 700))
    proof_line = (
        "Language balance, runtime routes, replay frames, and artifacts "
        "are generated from proof files."
    )
    parts.append(text(72, 134, proof_line, 17, "muted", 400))
    y = 178
    colors = [
        PALETTE["blue"],
        PALETTE["jade"],
        PALETTE["rose"],
        PALETTE["copper"],
        PALETTE["lilac"],
    ]
    ordered_languages = sorted(languages.items(), key=lambda item: item[1], reverse=True)
    for index, (language, count) in enumerate(ordered_languages):
        width = int(620 * (count / max_count))
        color = colors[index % len(colors)]
        parts.append(label(82, y + 18, language, 12, "muted"))
        parts.append(f'<rect x="250" y="{y}" width="660" height="22" rx="11" fill="#ffffff12"/>')
        parts.append(
            f'<rect x="250" y="{y}" width="{max(width, 10)}" height="22" '
            f'rx="11" fill="{color}" opacity="0.86"/>'
        )
        parts.append(text(930, y + 18, str(count), 18, "cream", 700))
        y += 42
    stat_x = 980
    stats = [
        ("artifact", benchmark.get("verification_artifact_count", 0), PALETTE["rose"]),
        ("stages", benchmark.get("stage_count", 0), PALETTE["jade"]),
        ("replay", benchmark.get("replay_frame_count", 0), PALETTE["blue"]),
    ]
    for index, (name, value, color) in enumerate(stats):
        parts.append(metric_card(stat_x, 170 + index * 82, name, str(value), color))
    write_svg("proof-bars.svg", "\n".join(parts), 1200, 420, "Proof metrics")


def export_music_privacy_panel() -> None:
    music = load_json("music-observatory.json")
    privacy = load_json("privacy-membrane.json")
    overview = music.get("overview", {})
    drift = music.get("drift", {})
    taxonomy = privacy.get("taxonomy", {})
    indicators = drift.get("indicators", [])[:5]
    parts = ['<rect width="1200" height="430" rx="34" fill="url(#atlas)"/>']
    parts.append(label(72, 72, "signal care", 14, "copper"))
    parts.append(
        text(
            72,
            104,
            "Audio and privacy are measured without storing what should stay private.",
            28,
            "cream",
            700,
        )
    )
    cards = [
        ("manifests", overview.get("manifest_count", 0), PALETTE["copper"]),
        ("segments", overview.get("total_segments", 0), PALETTE["jade"]),
        ("privacy types", taxonomy.get("category_count", 0), PALETTE["rose"]),
        ("languages", taxonomy.get("language_count", 0), PALETTE["blue"]),
    ]
    x = 72
    for name, value, color in cards:
        parts.append(metric_card(x, 144, name, str(value), color))
        x += 176
    y = 276
    parts.append(label(72, y - 18, "sound drift indicators", 12, "muted"))
    for index, indicator in enumerate(indicators):
        score = float(indicator.get("score", 0.0))
        label_text = str(indicator.get("label", "indicator"))[:32]
        width = int(360 * min(max(score, 0.0), 1.0))
        drift_colors = [
            PALETTE["jade"],
            PALETTE["copper"],
            PALETTE["rose"],
            PALETTE["blue"],
            PALETTE["lilac"],
        ]
        color = drift_colors[index % len(drift_colors)]
        parts.append(text(72, y + index * 28, label_text, 15, "cream", 600))
        bar_y = y - 14 + index * 28
        parts.append(rect(360, bar_y, 380, 12, "#ffffff12", 6))
        parts.append(rect(360, bar_y, max(width, 8), 12, color, 6, 0.86))
    parts.append(
        rounded_rect(800, 144, 315, 214, "rgba(255,255,255,0.055)", "#ffffff24", 28)
    )
    parts.append('<rect x="800" y="144" width="315" height="3" rx="1.5" fill="url(#softLine)"/>')
    parts.append(text(828, 190, "Receipt posture", 25, "cream", 700))
    parts.append(text(828, 226, "Raw media is referenced, not committed.", 17, "muted", 400))
    parts.append(text(828, 258, "Features, masks, hashes, and counts are kept.", 17, "muted", 400))
    parts.append(text(828, 290, "Small signals remain inspectable.", 17, "muted", 400))
    parts.append(
        (
            '<circle cx="1042" cy="320" r="44" fill="url(#glow)">'
            '<animate attributeName="r" values="36;48;36" dur="6s" '
            'repeatCount="indefinite"/></circle>'
        )
    )
    write_svg(
        "music-privacy-panel.svg",
        "\n".join(parts),
        1200,
        430,
        "Music and privacy evidence",
    )


def main() -> None:
    export_signal_atlas()
    export_runtime_map()
    export_proof_bars()
    export_music_privacy_panel()


if __name__ == "__main__":
    main()
