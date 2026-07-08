#!/usr/bin/env python3
"""Render a README workflow demo SVG for KeySurgeon."""

from __future__ import annotations

from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "assets" / "keysurgeon-flow.svg"


FRAMES = [
    {
        "tag": "01",
        "title": "Watch the signal",
        "command": "keysurgeon watch",
        "accent": "#00d7e6",
        "lines": [
            ("signal", "E key bounced 2 hit(s) while typing"),
            ("health", "evidence bar: 67/100, chatter rising"),
            ("privacy", "labels and timing only, no typed text"),
        ],
    },
    {
        "tag": "02",
        "title": "Diagnose the failure",
        "command": "keysurgeon test E",
        "accent": "#ff5a4d",
        "lines": [
            ("fault", "CHATTER DETECTED - E - 35/100"),
            ("proof", "re-press 31ms after release"),
            ("next", "run keysurgeon fix E"),
        ],
    },
    {
        "tag": "03",
        "title": "Repair in order",
        "command": "keysurgeon fix E",
        "accent": "#41d982",
        "lines": [
            ("1", "software filter"),
            ("2", "blow out debris"),
            ("3", "clean contact"),
            ("4", "hot-swap the switch"),
        ],
    },
    {
        "tag": "04",
        "title": "Check the proof",
        "command": "keysurgeon proof --json",
        "accent": "#f5b83d",
        "lines": [
            ("assets", "demo provenance hashes verified"),
            ("privacy", "no typed text stored or exported"),
            ("blocked", "hardware smoke not recorded yet"),
        ],
    },
]


def text(x: int, y: int, value: str, cls: str = "", fill: str | None = None) -> str:
    attrs = f' x="{x}" y="{y}"'
    if cls:
        attrs += f' class="{cls}"'
    if fill:
        attrs += f' fill="{fill}"'
    return f"<text{attrs}>{escape(value)}</text>"


def frame(index: int, item: dict[str, object]) -> str:
    x = 34 + (index % 2) * 589
    y = 128 + (index // 2) * 260
    accent = str(item["accent"])
    parts = [
        f'<g class="frame frame-{index + 1}">',
        f'<rect x="{x}" y="{y}" width="548" height="220" rx="18" fill="#111820" stroke="{accent}" stroke-width="2"/>',
        f'<rect x="{x + 18}" y="{y + 18}" width="52" height="28" rx="14" fill="{accent}" opacity="0.18"/>',
        text(x + 35, y + 38, str(item["tag"]), "tag", accent),
        text(x + 88, y + 40, str(item["title"]), "frame-title"),
        f'<rect x="{x + 24}" y="{y + 62}" width="500" height="36" rx="10" fill="#081116" stroke="#1f3440"/>',
        text(x + 44, y + 86, "$ " + str(item["command"]), "mono command"),
    ]
    line_y = y + 126
    for label, value in item["lines"]:  # type: ignore[index]
        parts.extend([
            text(x + 44, line_y, str(label).rjust(8), "mono label", accent),
            text(x + 132, line_y, str(value), "mono body"),
        ])
        line_y += 30
    parts.append("</g>")
    return "\n".join(parts)


def main() -> None:
    frames = "\n".join(frame(i, item) for i, item in enumerate(FRAMES))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1240" height="720" viewBox="0 0 1240 720" role="img" aria-labelledby="title desc">
  <title id="title">KeySurgeon workflow demo</title>
  <desc id="desc">Generated workflow demo showing watch, diagnosis, repair, and readiness commands.</desc>
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="#071013"/>
      <stop offset="0.48" stop-color="#122026"/>
      <stop offset="1" stop-color="#11110d"/>
    </linearGradient>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="18" stdDeviation="22" flood-color="#000000" flood-opacity="0.34"/>
    </filter>
  </defs>
  <style>
    .title {{ font: 800 54px Sora, Segoe UI, sans-serif; fill: #f6fbff; }}
    .subtitle {{ font: 500 18px Sora, Segoe UI, sans-serif; fill: #a9bac2; }}
    .frame-title {{ font: 800 24px Sora, Segoe UI, sans-serif; fill: #f6fbff; }}
    .tag {{ font: 800 15px Sora, Segoe UI, sans-serif; }}
    .mono {{ font: 500 18px JetBrains Mono, Cascadia Mono, Consolas, monospace; }}
    .command {{ fill: #f6fbff; }}
    .label {{ font-size: 15px; font-weight: 800; }}
    .body {{ fill: #d7e4e8; font-size: 16px; }}
    .rail {{ stroke-dasharray: 12 14; animation: dash 4.8s linear infinite; }}
    .pulse {{ animation: pulse 2.2s ease-in-out infinite; transform-origin: center; }}
    .frame {{ filter: url(#soft); }}
    .frame-1 {{ animation: lift1 8s ease-in-out infinite; }}
    .frame-2 {{ animation: lift2 8s ease-in-out infinite; }}
    .frame-3 {{ animation: lift3 8s ease-in-out infinite; }}
    .frame-4 {{ animation: lift4 8s ease-in-out infinite; }}
    @keyframes dash {{ to {{ stroke-dashoffset: -104; }} }}
    @keyframes pulse {{ 0%, 100% {{ opacity: .7; }} 50% {{ opacity: 1; }} }}
    @keyframes lift1 {{ 0%, 18% {{ transform: translateY(-6px); }} 28%, 100% {{ transform: translateY(0); }} }}
    @keyframes lift2 {{ 0%, 22% {{ transform: translateY(0); }} 32%, 48% {{ transform: translateY(-6px); }} 58%, 100% {{ transform: translateY(0); }} }}
    @keyframes lift3 {{ 0%, 52% {{ transform: translateY(0); }} 62%, 74% {{ transform: translateY(-6px); }} 84%, 100% {{ transform: translateY(0); }} }}
    @keyframes lift4 {{ 0%, 78% {{ transform: translateY(0); }} 88%, 100% {{ transform: translateY(-6px); }} }}
  </style>
  <rect width="1240" height="720" fill="url(#bg)"/>
  <circle class="pulse" cx="1118" cy="78" r="58" fill="#00d7e6" opacity="0.12"/>
  <circle class="pulse" cx="1118" cy="78" r="26" fill="#41d982" opacity="0.32"/>
  {text(34, 72, "KeySurgeon", "title")}
  {text(38, 105, "A terminal workflow for catching keyboard chatter, choosing the repair, and checking what is ready.", "subtitle")}
  <path class="rail" d="M585 238 C650 238 574 386 634 386 M614 238 C682 238 608 386 666 386" fill="none" stroke="#2a4650" stroke-width="4"/>
  {frames}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"KEYSURGEON_FLOW_SVG_OK {OUT} {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
