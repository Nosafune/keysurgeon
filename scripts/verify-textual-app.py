#!/usr/bin/env python3
"""Headless runtime smoke for the optional Textual app."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from textual.widgets import Static

import app_textual


SNAPSHOT = {
    "ts": "2026-07-01T00:00:00",
    "keys": [
        {"label": "E", "score": 35, "fault": "chatter"},
        {"label": "R", "score": 88, "fault": "watch"},
        {"label": "T", "score": 97, "fault": "healthy"},
    ],
}

PROOF_PAYLOAD = {
    "local_proof": {
        "demo_assets": {"status": "ok", "assets": ["demo", "app"]},
        "manual_keyboard_smoke": {
            "status": "blocked",
            "detail": "real keyboard smoke not recorded",
        },
        "rich_textual_stack": {"status": "ok", "detail": "Rich and Textual import"},
        "package_build_gate": {
            "status": "command-gated",
            "command": "scripts/release-check.ps1",
        },
        "proof_matrix": {"status": "local-ready"},
        "release_package": {"status": "blocked", "detail": "not published"},
    },
    "proof_summary": {"local": 7, "command_gated": 1, "blocked": 4},
    "public_blockers": ["real keyboard smoke must be recorded"],
}


def _rendered_text(app, selector):
    content = app.query_one(selector, Static).content
    plain = getattr(content, "plain", None)
    return plain if plain is not None else str(content)


async def _run_smoke():
    calls = {"start": 0, "stop": 0}
    originals = {
        "is_running": app_textual.watch.is_running,
        "read_state": app_textual.watch.read_state,
        "start_background": app_textual.watch.start_background,
        "stop_background": app_textual.watch.stop_background,
        "latest": app_textual.profile.latest,
        "detect_keyboards": app_textual.boards.detect_keyboards,
        "build_payload": app_textual.proof_report.build_payload,
    }

    running = {"value": False}

    def is_running():
        return running["value"], 4321 if running["value"] else None

    def read_state():
        if not running["value"]:
            return {}
        return {
            "updated": "2026-07-01T00:00:03",
            "keys": {"E": {"bounces": 3, "presses": 12}},
        }

    def start_background(keyboard):
        calls["start"] += 1
        running["value"] = True
        return True, f"watch started for {keyboard}"

    def stop_background():
        calls["stop"] += 1
        running["value"] = False
        return True, "watch stopped"

    try:
        app_textual.watch.is_running = is_running
        app_textual.watch.read_state = read_state
        app_textual.watch.start_background = start_background
        app_textual.watch.stop_background = stop_background
        app_textual.profile.latest = lambda keyboard: (SNAPSHOT, "hotswap")
        app_textual.boards.detect_keyboards = lambda: [{
            "vid": "3434",
            "pid": "0112",
            "vendor": "Keychron",
            "product": "Keychron Q1",
            "role": "keyboard",
            "hint": "Keychron - often hot-swappable mechanical (confirm below)",
        }]
        app_textual.proof_report.build_payload = lambda: PROOF_PAYLOAD

        app = app_textual.build_app("pilot-kb")
        if app is None:
            raise AssertionError("Textual app factory returned None")

        async with app.run_test(size=(120, 42)) as pilot:
            await pilot.pause()
            required = {
                "#hero": ("KeySurgeon", "No typed text stored"),
                "#rail": ("FORENSIC SIGNAL RAIL", "watch"),
                "#command": ("COMMAND CENTER", "keysurgeon fix E"),
                "#device": ("DEVICE", "repair model:", "hotswap"),
                "#readiness": ("READINESS", "hardware:", "blocked"),
                "#actions": ("ACTION BAR", "issue packet", "No fake repair buttons"),
                "#issue": ("ISSUE PACKET", "keysurgeon issue", "no typed text is stored or exported"),
                "#commands": ("KEYS", "CLI FLOW", "keysurgeon proof --json"),
            }
            for selector, needles in required.items():
                text = _rendered_text(app, selector)
                missing = [needle for needle in needles if needle not in text]
                if missing:
                    raise AssertionError(f"{selector} missing {missing}: {text!r}")

            await pilot.press("p")
            await pilot.pause()
            assert "keysurgeon proof --json" in _rendered_text(app, "#message")

            await pilot.press("i")
            await pilot.pause()
            assert "keysurgeon issue" in _rendered_text(app, "#message")

            await pilot.press("w")
            await pilot.pause()
            assert calls["start"] == 1, calls
            assert "watch started for pilot-kb" in _rendered_text(app, "#message")
            assert "armed" in _rendered_text(app, "#signal")
            assert "bouncing in watch mode" in _rendered_text(app, "#command")

        print("KEYSURGEON_TEXTUAL_APP_SMOKE_OK")
    finally:
        app_textual.watch.is_running = originals["is_running"]
        app_textual.watch.read_state = originals["read_state"]
        app_textual.watch.start_background = originals["start_background"]
        app_textual.watch.stop_background = originals["stop_background"]
        app_textual.profile.latest = originals["latest"]
        app_textual.boards.detect_keyboards = originals["detect_keyboards"]
        app_textual.proof_report.build_payload = originals["build_payload"]


if __name__ == "__main__":
    asyncio.run(_run_smoke())
