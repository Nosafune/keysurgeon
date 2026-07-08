#!/usr/bin/env python3
"""Render the public app-mode signal rail SVG from KeySurgeon's app renderer."""

from pathlib import Path
import io
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

import app_textual
import brand
import faults
from demo_svg_format import CHROMELESS_SVG_FORMAT


def main():
    out = ROOT / "site" / "assets" / "keysurgeon-app.svg"
    console = Console(
        record=True,
        width=92,
        color_system="truecolor",
        theme=Theme(brand.RICH_THEME),
        file=io.StringIO(),
    )

    snapshot = {
        "ts": "sample report",
        "keys": [
            {"label": "E", "fault": faults.CHATTER, "score": 35},
            {"label": "I", "fault": faults.INTERMITTENT, "score": 72},
            {"label": "Q", "fault": faults.OK, "score": 100},
            {"label": "R", "fault": faults.OK, "score": 100},
        ],
    }
    readiness_payload = {
        "local_proof": {
            "demo_assets": {
                "status": "ok",
                "detail": "generated demo assets match recorded hashes",
                "assets": ["demo", "demo-png", "app", "app-png", "flow", "social", "landing-desktop", "landing-mobile"],
            },
            "manual_keyboard_smoke": {
                "status": "blocked",
                "detail": "real keyboard smoke is not run",
            },
            "rich_textual_stack": {
                "status": "ok",
                "detail": "Rich/Textual demos and bitmap captures are hash-verified; Textual runtime smoke is gated by scripts/verify-textual-app.py",
            },
            "proof_matrix": {
                "status": "ok",
                "detail": "docs/PROOF_MATRIX.md maps local-ready, command-gated, and blocked public claims",
            },
        },
        "proof_summary": {"local": 8, "command_gated": 1, "blocked": 1},
        "public_blockers": [
            "manual keyboard smoke must record hardware-smoke-pass before broad hardware claims",
        ],
    }

    original_running = app_textual.watch.is_running
    original_state = app_textual.watch.read_state
    original_latest = app_textual.profile.latest
    original_detect = app_textual.boards.detect_keyboards
    try:
        app_textual.watch.is_running = lambda: (True, 4321)
        app_textual.watch.read_state = lambda: {
            "updated": "sample watcher state",
            "keys": {
                "E": {"bounces": 2, "presses": 42},
                "I": {"bounces": 1, "presses": 33},
            },
        }
        app_textual.profile.latest = lambda keyboard: (snapshot, "hotswap")
        app_textual.boards.detect_keyboards = lambda: [{
            "vid": "3434",
            "pid": "0111",
            "vendor": "Keychron",
            "product": "Keychron Q1",
            "keys_total": 104,
            "role": "keyboard",
            "hint": "Keychron - often hot-swappable mechanical (confirm below)",
        }]
        content = Group(
            Text.from_markup(app_textual._hero_text(snapshot)),
            Text(""),
            Text.from_markup(app_textual._signal_rail(snapshot)),
            Text(""),
            Text.from_markup(app_textual._command_center(snapshot)),
            Text(""),
            Text.from_markup(app_textual._device_text("sample")),
            Text(""),
            Text.from_markup(app_textual._readiness_text(readiness_payload)),
            Text(""),
            Text.from_markup(app_textual._repair_ladder()),
            Text(""),
            Text.from_markup(app_textual._action_bar()),
            Text(""),
            Text.from_markup(app_textual._issue_packet_text()),
            Text(""),
            Text.from_markup(app_textual._commands()),
            Text(""),
            Text.from_markup(app_textual._health_map(snapshot)),
        )
        console.print(Panel(
            content,
            title=f"{brand.SIGNAL_MARK} {brand.NAME} app",
            subtitle="seeded sample state",
            border_style="ks.signal",
            padding=(1, 2),
        ))
    finally:
        app_textual.watch.is_running = original_running
        app_textual.watch.read_state = original_state
        app_textual.profile.latest = original_latest
        app_textual.boards.detect_keyboards = original_detect

    out.write_text(
        console.export_svg(
            title="KeySurgeon Textual command center demo",
            code_format=CHROMELESS_SVG_FORMAT,
        ),
        encoding="utf-8",
    )
    print(f"KEYSURGEON_APP_SVG_OK {out} {out.stat().st_size} bytes")


if __name__ == "__main__":
    main()
