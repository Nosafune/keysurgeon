#!/usr/bin/env python3
"""Terminal rendering for KeySurgeon.

The "human feel" layer: plain-language headlines, dimmed evidence, ranked fixes,
and a color heatmap. House palette (chocolate-orange accent). Color + glyphs
degrade gracefully (--no-color, NO_COLOR env, ASCII fallback).
"""

import ctypes
import ctypes.wintypes as wt
import os
import sys
import textwrap

from faults import band

# palette (256-color)
_RAW = {
    "RST": "\x1b[0m", "BLD": "\x1b[1m",
    "ACC": "\x1b[38;5;208m",   # chocolate orange
    "OK": "\x1b[38;5;114m",    # green
    "BAD": "\x1b[38;5;203m",   # red
    "WRN": "\x1b[38;5;179m",   # amber
    "DIM": "\x1b[38;5;245m",   # grey
}

USE_COLOR = True
USE_GLYPHS = True


def init(use_color=True, use_glyphs=True):
    global USE_COLOR, USE_GLYPHS
    USE_COLOR = use_color and not os.environ.get("NO_COLOR")
    USE_GLYPHS = use_glyphs
    if USE_COLOR:  # enable ANSI on the Windows console
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


# band -> color name
_BAND_COLOR = {"HEALTHY": "OK", "WATCH": "WRN", "DEGRADING": "WRN", "FAILING": "BAD"}


def score_color(score):
    return _BAND_COLOR.get(band(score), "DIM")


def banner(subtitle=""):
    dot = g("", "#")  # nf keyboard glyph, ascii '#'
    line = c("KeySurgeon", "BLD", "ACC")
    if subtitle:
        line += "  " + c(g("·", "-"), "DIM") + "  " + c(subtitle, "DIM")
    print("\n  " + line + "\n")


MENU_ITEMS = [
    ("1", "triage", "Triage", "something's wrong - walk me through it"),
    ("2", "sweep", "Sweep", "check the whole board (live heatmap)"),
    ("3", "watch", "Watch", "run in the background, tell me what's dying"),
    ("4", "test", "Test", "test specific keys right now"),
    ("5", "report", "Report", "how's my board doing? (last results + trend)"),
    ("6", "fix", "Fix", "show the fix ladder for one key"),
]


def menu():
    banner("pick a mode")
    for num, _mode, title, blurb in MENU_ITEMS:
        print("    " + c(num, "BLD", "ACC") + "  "
              + c(f"{title:<8}", "BLD") + c(blurb, "DIM"))
    print("\n    " + c("q", "DIM") + "  " + c("quit", "DIM"))
    return input("\n  " + c("pick a number", "ACC") + c(" › ", "DIM"))


def live_counter(label, n, expected):
    full = n >= expected
    col = "OK" if full else "ACC"
    bar = c(f"{n:>2}", "BLD", col) + c(f"/{expected}", "DIM")
    hint = c("press until the counter fills - ESC skips", "DIM")
    sys.stdout.write("\r  " + c(f"[{label}]", "BLD", "ACC") + "  " + bar
                     + "   " + hint + "   ")
    sys.stdout.flush()


def _wrap(text, width=48):
    return textwrap.wrap(text, width)


def card(verdict, rungs, closer):
    """Boxed per-key card: headline, detail, dimmed evidence, ranked fixes."""
    label = verdict["label"]
    bnd = band(verdict["score"])
    bcol = score_color(verdict["score"])
    W = 52
    tl, tr, bl, br = (g("┌", "+"), g("┐", "+"),
                      g("└", "+"), g("┘", "+"))
    h, v = g("─", "-"), g("│", "|")

    head = f" {label} "
    tag = f" {bnd} "
    fill = W - len(head) - len(tag) - 2
    print()
    print("  " + c(tl + h + head, "DIM") + c(h * fill, "DIM")
          + c(tag, "BLD", bcol) + c(h + tr, "DIM"))

    def row(s=""):
        print("  " + c(v, "DIM") + "  " + s)

    row(c(verdict["headline"], "BLD"))
    for ln in _wrap(verdict["detail"]):
        row(ln)
    if verdict.get("confidence") == "low":
        row()
        for ln in _wrap("Only a few presses seen - run it again for a "
                        "confident read."):
            row(c(ln, "WRN"))
    row()
    ev = verdict["evidence"]
    if ev:
        row(c("evidence", "DIM") + c(" · " if USE_GLYPHS else " - ", "DIM")
            + c(ev[0], "DIM"))
        for e in ev[1:]:
            row(c("         " + g("·", "-") + " ", "DIM") + c(e, "DIM"))

    if rungs:
        row()
        row(c("What to do, easiest first:", "BLD"))
        for n, title, blurb in rungs:
            row(c(f"  {n}  ", "ACC") + c(title, "BLD"))
            for ln in _wrap(blurb, 44):
                row(c("     " + ln, "DIM"))
    if closer:
        row()
        row(c(closer, "OK") if verdict["score"] > 0 else c(closer, "WRN"))
    print("  " + c(bl + h * (W - 1) + br, "DIM"))


# keyboard layout for the heatmap (labels match trial labels)
_LAYOUT = [
    list("1234567890"),
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
]


def heatmap(score_by_label, title="board health"):
    banner(title)
    pad = {0: "", 1: " ", 2: "  ", 3: "   "}
    for i, rowkeys in enumerate(_LAYOUT):
        cells = []
        for k in rowkeys:
            if k in score_by_label:
                cells.append(c(f" {k} ", "BLD", score_color(score_by_label[k])))
            else:
                cells.append(c(f" {k} ", "DIM"))
        print("   " + pad[i] + " ".join(cells))
    dot = g("●", "*")
    legend = "   ".join([
        c(dot, "OK") + " healthy", c(dot, "WRN") + " watch",
        c(dot, "WRN") + " degrading", c(dot, "BAD") + " failing",
        c(dot, "DIM") + " untested",
    ])
    print("\n   " + legend + "\n")


def report(snapshot, board_type):
    banner("board report")
    if not snapshot:
        print("  " + c("No saved results yet.", "DIM"))
        print("  " + c("Run a sweep or test first, then check back.", "DIM") + "\n")
        return
    keys = snapshot["keys"]
    scores = [k["score"] for k in keys] or [100]
    avg = sum(scores) // len(scores)
    bnd = band(avg)
    bad = sorted([k for k in keys if k["score"] < 90], key=lambda k: k["score"])

    print("  " + c(f"Board: {bnd}", "BLD", score_color(avg))
          + c(f"   avg {avg}/100  ({len(keys)} keys tested, "
              f"{snapshot['ts']})", "DIM"))
    print("  " + c(f"Keyboard type: {board_type}", "DIM") + "\n")
    if not bad:
        print("  " + c("Every tested key is healthy. Nothing to fix.", "OK") + "\n")
        return
    print("  " + c("Keys that need attention:", "BLD"))
    for k in bad:
        print("    " + c(f"{k['label']:<3}", "BLD", score_color(k["score"]))
              + c(f" {k['fault']:<13}", score_color(k["score"]))
              + c(f"score {k['score']}", "DIM"))
    worst = bad[0]
    print("\n  " + c("Most important next step: ", "BLD")
          + c(f"check {worst['label']} ({worst['fault']}) - "
              f"run  keysurgeon fix {worst['label']}", "ACC") + "\n")
