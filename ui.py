#!/usr/bin/env python3
"""Terminal rendering for KeySurgeon.

Rich powers the default v2 surface. --plain / --no-color falls back to this
dependency-light ANSI/ASCII renderer so automation never has to parse styled UI.
"""

import ctypes
import ctypes.wintypes as wt
import os
import sys
import textwrap

import brand
from faults import band

try:
    import rich_ui
except Exception:  # pragma: no cover - fallback path is intentionally broad
    rich_ui = None

_RAW = {
    "RST": "\x1b[0m",
    "BLD": "\x1b[1m",
    "ACC": "\x1b[38;5;51m",    # signal cyan
    "OK": "\x1b[38;5;84m",     # repair green
    "BAD": "\x1b[38;5;203m",   # fault coral
    "WRN": "\x1b[38;5;221m",   # probe amber
    "DIM": "\x1b[38;5;245m",
}

USE_COLOR = True
USE_GLYPHS = True
USE_RICH = False


def init(use_color=True, use_glyphs=True):
    global USE_COLOR, USE_GLYPHS, USE_RICH
    USE_COLOR = use_color and not os.environ.get("NO_COLOR")
    USE_GLYPHS = use_glyphs
    USE_RICH = bool(USE_COLOR and USE_GLYPHS and rich_ui)
    if USE_COLOR:
        h = ctypes.windll.kernel32.GetStdHandle(-11)
        mode = wt.DWORD()
        if ctypes.windll.kernel32.GetConsoleMode(h, ctypes.byref(mode)):
            ctypes.windll.kernel32.SetConsoleMode(h, mode.value | 0x0004)


def _esc(name):
    return _RAW[name] if USE_COLOR else ""


def c(text, *names):
    if not USE_COLOR:
        return str(text)
    return "".join(_esc(n) for n in names) + str(text) + _esc("RST")


def g(glyph, ascii_fallback):
    return glyph if USE_GLYPHS else ascii_fallback


_BAND_COLOR = {
    "HEALTHY": "OK",
    "WATCH": "WRN",
    "DEGRADING": "WRN",
    "FAILING": "BAD",
}


def score_color(score):
    return _BAND_COLOR.get(band(score), "DIM")


def banner(subtitle=""):
    if USE_RICH:
        return rich_ui.banner(subtitle)
    line = c(brand.SIGNAL_MARK + "  " + brand.NAME, "BLD", "ACC")
    if subtitle:
        line += "  " + c("/", "DIM") + "  " + c(subtitle, "DIM")
    print("\n  " + line + "\n")


MENU_ITEMS = [
    ("0", "tour", "Tour", "first-run command center and proof gates"),
    ("1", "triage", "Triage", "something's wrong, walk me through it"),
    ("2", "sweep", "Sweep", "check the whole board"),
    ("3", "watch", "Watch", "tell me what's dying while I type"),
    ("4", "test", "Test", "test specific keys right now"),
    ("5", "report", "Report", "latest board health and trend"),
    ("6", "fix", "Fix", "show the repair ladder for one key"),
    ("7", "ready", "Ready", "launch readiness board"),
    ("8", "proof", "Proof", "full local proof and blockers"),
    ("9", "app", "App", "open the optional Textual command center"),
    ("d", "doctor", "Doctor", "check install and support facts"),
]


def menu():
    if USE_RICH:
        rich_ui.menu(MENU_ITEMS)
        return input("  pick a number > ")
    banner("pick a mode")
    for num, _mode, title, blurb in MENU_ITEMS:
        print("    " + c(num, "BLD", "ACC") + "  "
              + c(f"{title:<8}", "BLD") + c(blurb, "DIM"))
    print("\n    " + c("q", "DIM") + "  " + c("quit", "DIM"))
    return input("\n  " + c("pick a number", "ACC") + c(" > ", "DIM"))


def tour(payload):
    if USE_RICH:
        return rich_ui.tour(payload)
    banner("first-run tour")
    proof = payload["local_proof"]
    summary = payload.get("proof_summary") or {}
    print("  " + c("What it is: ", "BLD") + "keyboard chatter and fault diagnosis")
    print("  " + c("Core loop: ", "BLD") + "watch -> test -> fix -> proof")
    print("  " + c("App shell: ", "BLD", "ACC") + "keysurgeon app")
    print("  " + c("Privacy: ", "BLD") + "local JSON only; no typed text exported")
    print()
    rows = [
        ("1", "keysurgeon watch --bg", "catch double-fires while you type normally"),
        ("2", "keysurgeon test E", "turn suspicion into a timed verdict"),
        ("3", "keysurgeon fix E", "show the cheapest-first repair ladder"),
        ("4", "keysurgeon proof --json", "see exactly what is and is not proved"),
        ("5", "keysurgeon issue", "write a redacted GitHub-ready packet"),
    ]
    for num, command, why in rows:
        print("  " + c(num, "ACC", "BLD") + "  " + c(f"{command:<28}", "BLD") + c(why, "DIM"))
    print()
    gates = [
        ("Rich/Textual", proof["rich_textual_stack"]),
        ("Public assets", proof["demo_assets"]),
        ("Package metadata", proof["package_metadata"]),
        ("Package gate", proof["package_build_gate"]),
        ("Release package", proof["release_package"]),
        ("Hardware smoke", proof["manual_keyboard_smoke"]),
    ]
    print("  " + c(
        f"Readiness: local {summary.get('local', 0)}  "
        f"command-gated {summary.get('command_gated', 0)}  "
        f"blocked {summary.get('blocked', 0)}",
        "BLD",
    ))
    for label, item in gates:
        print("    " + c(f"{item['status']:<13}", _proof_status_style(item["status"]), "BLD")
              + f" {label:<16} {item['detail']}")
    blockers = payload.get("public_blockers") or []
    if blockers:
        print()
        print("  " + c("Not claimed yet:", "WRN", "BLD"))
        for blocker in blockers:
            print("    " + c("- ", "WRN") + blocker)
    print()


def live_counter(label, n, expected):
    if USE_RICH:
        return rich_ui.live_counter(label, n, expected)
    full = n >= expected
    col = "OK" if full else "ACC"
    filled = min(12, int((n / max(expected, 1)) * 12))
    bar = "[" + ("#" * filled).ljust(12, ".") + "]"
    sys.stdout.write("\r  " + c(f"[{label}]", "BLD", "ACC") + "  "
                     + c(bar, col) + f" {n:>2}/{expected}"
                     + c("  ESC skips", "DIM") + "   ")
    sys.stdout.flush()


def _wrap(text, width=48):
    return textwrap.wrap(text, width)


def card(verdict, rungs, closer):
    if USE_RICH:
        return rich_ui.card(verdict, rungs, closer)
    label = verdict["label"]
    bnd = band(verdict["score"])
    bcol = score_color(verdict["score"])
    width = 54
    head = f" {label} "
    tag = f" {bnd} "
    fill = width - len(head) - len(tag) - 2
    print()
    print("  " + c("+" + "-" + head, "DIM") + c("-" * fill, "DIM")
          + c(tag, "BLD", bcol) + c("-+", "DIM"))

    def row(s=""):
        print("  " + c("|", "DIM") + "  " + s)

    row(c(verdict["headline"], "BLD"))
    for line in _wrap(verdict["detail"]):
        row(line)
    if verdict.get("confidence") == "low":
        row()
        for line in _wrap("Only a few presses seen. Run it again for a confident read."):
            row(c(line, "WRN"))
    evidence = verdict.get("evidence") or []
    if evidence:
        row()
        row(c("evidence - ", "DIM") + c(evidence[0], "DIM"))
        for item in evidence[1:]:
            row(c("           - " + item, "DIM"))
    if rungs:
        row()
        row(c("What to do, easiest first:", "BLD"))
        for n, title, blurb in rungs:
            row(c(f"  {n}  ", "ACC") + c(title, "BLD"))
            for line in _wrap(blurb, 44):
                row(c("     " + line, "DIM"))
    if closer:
        row()
        row(c(closer, "OK") if verdict["score"] > 0 else c(closer, "WRN"))
    print("  " + c("+" + "-" * (width - 1) + "+", "DIM"))


def heatmap(score_by_label, title="board health"):
    if USE_RICH:
        return rich_ui.heatmap(score_by_label, title)
    banner(title)
    rows = ["1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    for offset, rowkeys in enumerate(rows):
        cells = []
        for key in rowkeys:
            if key in score_by_label:
                cells.append(c(f" {key} ", "BLD", score_color(score_by_label[key])))
            else:
                cells.append(c(f" {key} ", "DIM"))
        print("   " + (" " * offset) + " ".join(cells))
    print("\n   " + c("+ healthy", "OK") + "   " + c("! watch", "WRN")
          + "   " + c("x failing", "BAD") + "   " + c(". untested", "DIM") + "\n")


def report(snapshot, board_type):
    if USE_RICH:
        return rich_ui.report(snapshot, board_type)
    banner("board report")
    if not snapshot:
        print("  " + c("No saved results yet.", "DIM"))
        print("  " + c("Run a sweep or test first, then check back.", "DIM") + "\n")
        return
    keys = snapshot["keys"]
    scores = [item["score"] for item in keys] or [100]
    avg = sum(scores) // len(scores)
    bnd = band(avg)
    bad = sorted([item for item in keys if item["score"] < 90],
                 key=lambda item: item["score"])

    print("  " + c(f"Board: {bnd}", "BLD", score_color(avg))
          + c(f"   avg {avg}/100  ({len(keys)} keys tested, {snapshot['ts']})", "DIM"))
    print("  " + c(f"Keyboard type: {board_type}", "DIM") + "\n")
    if not bad:
        print("  " + c("Every tested key is healthy. Nothing to fix.", "OK") + "\n")
        return
    print("  " + c("Keys that need attention:", "BLD"))
    for item in bad:
        print("    " + c(f"{item['label']:<3}", "BLD", score_color(item["score"]))
              + c(f" {item['fault']:<13}", score_color(item["score"]))
              + c(f"score {item['score']}", "DIM"))
    worst = bad[0]
    print("\n  " + c("Most important next step: ", "BLD")
          + c(f"check {worst['label']} ({worst['fault']}) - "
              f"run keysurgeon fix {worst['label']}", "ACC") + "\n")


def proof_report(payload):
    if USE_RICH:
        return rich_ui.proof_report(payload)
    banner("proof")
    print("  " + c(f"{payload['tool']} {payload['version']}", "BLD", "ACC"))
    print("  " + c(payload["privacy"], "DIM"))
    print()

    proof = payload["local_proof"]
    rows = [
        ("Rich/Textual demos", proof["demo_assets"]),
        ("Manual keyboard smoke", proof["manual_keyboard_smoke"]),
        ("Stack proof", proof["rich_textual_stack"]),
        ("Package metadata", proof["package_metadata"]),
        ("Package build gate", proof["package_build_gate"]),
        ("Claim matrix", proof["proof_matrix"]),
        ("Release package", proof["release_package"]),
    ]
    for label, item in rows:
        status = item["status"]
        print("  " + c(f"{status:<8}", _proof_status_style(status), "BLD")
              + f" {label:<24} {item['detail']}")

    matrix = payload.get("proof_matrix") or []
    if matrix:
        summary = payload.get("proof_summary") or {}
        print()
        print("  " + c("Claim matrix:", "BLD"))
        print("    " + c(
            f"local {summary.get('local', 0)}  "
            f"command-gated {summary.get('command_gated', 0)}  "
            f"blocked {summary.get('blocked', 0)}",
            "DIM",
        ))
        for item in matrix[:8]:
            tier_style = "WRN" if item["tier"] == "blocked" else ("ACC" if item["tier"] == "command_gated" else "OK")
            print("    " + c(f"{item['tier']:<13}", tier_style, "BLD")
                  + f" {item['claim']} -> {item['verifier']}")

    assets = proof["demo_assets"].get("assets") or []
    if assets:
        print()
        print("  " + c("Generated public assets:", "BLD"))
        for item in assets:
            status = item["status"]
            print("    " + c(f"{status:<6}", _proof_status_style(status), "BLD")
                  + f" {item['kind']:<28} {item['path']} ({item['bytes']} bytes)")

    print()
    print("  " + c("Not proved yet:", "WRN", "BLD"))
    for blocker in payload["public_blockers"]:
        print("    " + c("- ", "WRN") + blocker)
    print()


def ready_report(payload):
    if USE_RICH:
        return rich_ui.ready_report(payload)
    banner("launch readiness")
    summary = payload.get("proof_summary") or {}
    print("  " + c(
        f"Local proof: {summary.get('local', 0)} local / "
        f"{summary.get('command_gated', 0)} command-gated / "
        f"{summary.get('blocked', 0)} blocked",
        "BLD",
        "ACC",
    ))
    print("  " + c("Mode: local summary only; no git, GitHub, release, Pages, or deploy changes.", "DIM"))
    print()
    print("  " + c("Next safe actions:", "BLD"))
    for item in payload.get("next_actions") or []:
        remote = "remote" if item.get("changes_remote") else "local"
        print("    " + c(item["label"], "ACC", "BLD") + c(f"  ({remote})", "DIM"))
        print("      " + item["command"])
    blockers = payload.get("public_blockers") or []
    if blockers:
        print()
        print("  " + c("Still blocked:", "WRN", "BLD"))
        for blocker in blockers:
            print("    " + c("- ", "WRN") + blocker)
    print()


def _proof_status_style(status):
    if status == "ok":
        return "OK"
    if status == "missing":
        return "BAD"
    return "WRN"
