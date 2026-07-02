#!/usr/bin/env python3
"""Render the public terminal demo SVG from the actual Rich card renderer."""

from pathlib import Path
import io
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rich.console import Console
from rich.theme import Theme

import brand
import faults
import fixes
import rich_ui
from demo_svg_format import CHROMELESS_SVG_FORMAT


def main():
    out = ROOT / "site" / "assets" / "keysurgeon-demo.svg"
    console = Console(
        record=True,
        width=86,
        color_system="truecolor",
        theme=Theme(brand.RICH_THEME),
        file=io.StringIO(),
    )
    rich_ui.console = console

    verdict = {
        "fault": faults.CHATTER,
        "label": "E",
        "headline": "This key is double-typing.",
        "detail": "KeySurgeon saw repeated press timing that is too fast for normal typing.",
        "evidence": [
            "re-press 31ms",
            "18 bounces in 240 presses",
            "confidence: high",
        ],
        "score": 35,
        "confidence": "high",
    }
    rungs, closer = fixes.ladder_for(faults.CHATTER, fixes.HOTSWAP)
    rich_ui.card(verdict, rungs[:4], closer)

    out.write_text(
        console.export_svg(
            title="KeySurgeon terminal diagnosis demo",
            code_format=CHROMELESS_SVG_FORMAT,
        ),
        encoding="utf-8",
    )
    print(f"KEYSURGEON_DEMO_SVG_OK {out} {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
