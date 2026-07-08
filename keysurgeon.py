#!/usr/bin/env python3
"""KeySurgeon - guided keyboard diagnostic that finds fixable problems before
you replace the board.

Run with no args for a menu (you don't need to remember verbs):
    python keysurgeon.py

Or jump straight to a mode:
    python keysurgeon.py triage          # "what's wrong?" wizard
    python keysurgeon.py tour            # first-run command-center preview
    python keysurgeon.py sweep           # whole board + live heatmap
    python keysurgeon.py watch           # background-style live chatter watch
    python keysurgeon.py test E R T      # test specific keys now
    python keysurgeon.py report          # last results + board health
    python keysurgeon.py issue           # redacted GitHub issue packet
    python keysurgeon.py export          # redacted issue/repair report
    python keysurgeon.py proof           # full local proof/readiness report
    python keysurgeon.py site           # local landing/demo page
    python keysurgeon.py smoke          # manual hardware-smoke report scaffold
    python keysurgeon.py fix E           # fix ladder for one key
    python keysurgeon.py doctor          # support/environment check

Flags (any mode): --plain / --ai (no color, structured), --no-color,
    --keyboard <name>, --presses <n>

Windows only. Rich powers the default terminal UI; Textual provides optional
app mode when installed. See README.md for public usage.
"""

import shutil
import sys
import time
import webbrowser
from pathlib import Path

import brand
import boards
import faults
import fixes
import ks_profile as profile
import storage
import trials
import ui
import watch
from hook import KeyboardHook, to_vk, vk_name

VERSION = brand.VERSION
EROW = list("QWERTYUIOP")

HELP_TEXT = f"""{brand.NAME} {VERSION}

{brand.TAGLINE}

Usage:
  keysurgeon                         menu
  keysurgeon app                     optional Textual command center
  keysurgeon tour                    first-run command-center preview
  keysurgeon triage                  guided problem finder
  keysurgeon sweep                   full-board diagnostic
  keysurgeon watch [--bg|--status|--stop]
  keysurgeon test E R T              test specific keys
  keysurgeon report                  last results and trend
  keysurgeon issue [--out FILE]      redacted GitHub issue packet
  keysurgeon export [--json] [--out FILE]
                                    redacted report for GitHub issues
  keysurgeon proof [--json]             full local proof/readiness report
  keysurgeon site [--open]              local landing/demo page path
  keysurgeon smoke [--out FILE]         manual hardware-smoke report scaffold
  keysurgeon smoke --check FILE         validate filled smoke evidence report
  keysurgeon fix E                   repair ladder for one key
  keysurgeon board                   set keyboard type
  keysurgeon doctor                  support/environment check
  keysurgeon selftest                logic checks, no keyboard needed

Options:
  --plain, --ai                      plain output
  --no-color                         disable color
  --keyboard NAME                    separate profile name
  --presses N                        presses per trial, default 20
  --version                          print version
  -h, --help                         show this help

Runtime data:
  Per-user local JSON only. Override location with KEYSURGEON_HOME.
"""


# ---------- shared helpers ----------

def _run_one_key(hook, key, expected):
    """Run a chatter trial on one key, print live counter, return verdict or None."""
    try:
        vk = to_vk(key)
    except ValueError as e:
        print("  " + ui.c(str(e), "BAD"))
        return None
    label = key.upper()

    def progress(n, exp):
        ui.live_counter(label, n, exp)

    print()
    stats = trials.chatter_trial(hook, vk, label, expected, progress)
    if stats is None:
        print(ui.c("  skipped", "DIM"))
        return None
    print()
    return faults.classify(stats)


def _ask_board_type(default="unknown", force=False):
    """Resolve the keyboard's board type. Asks ONCE, then remembers it keyed by
    the detected hardware and never asks again (force=True re-asks)."""
    detected = boards.detect_keyboards()
    sig = boards.device_signature(detected)

    kbs = boards.keyboards_only(detected)

    if not force:
        saved = boards.recall_board_type(sig)
        if saved:
            desc = dict(fixes.BOARD_CHOICES).get(saved, saved)
            who = next((d["product"] for d in kbs if d.get("product")), "")
            tag = f" ({who})" if who else ""
            print("  " + ui.c(f"Keyboard: {desc}{tag}", "DIM")
                  + ui.c("  (remembered - change with  keysurgeon board)", "DIM"))
            return saved
        # known model -> resolve it ourselves, don't ask at all
        for d in kbs:
            bt = boards.infer_from_model(d.get("product"))
            if bt:
                boards.remember_board_type(sig, bt)
                desc = dict(fixes.BOARD_CHOICES).get(bt, bt)
                print("  " + ui.c(f"Detected {d['product']} -> {desc}.", "DIM")
                      + ui.c("  (auto - change with  keysurgeon board)", "DIM"))
                return bt

    # show what we found (real keyboards highlighted, mice flagged + ignored)
    if detected:
        print("\n  " + ui.c("Detected:", "DIM"))
        for d in detected:
            who = d.get("product") or d["vendor"] or "Unknown"
            if d["vid"]:
                tail = f"  (VID {d['vid']} PID {d['pid']})"
            else:
                tail = "  (built-in)"
            if d.get("role") == "keyboard":
                print("    " + ui.c(g_dot(), "ACC") + " " + ui.c(who, "BLD")
                      + ui.c(tail, "DIM"))
            else:
                print("    " + ui.c(g_dot(), "DIM") + " " + ui.c(who, "DIM")
                      + ui.c(tail + "  - not a keyboard, ignored", "DIM"))
    guess = boards.best_guess_type(detected)

    print("\n  " + ui.c("What kind of keyboard is this?", "BLD")
          + ui.c("  (asked once, then remembered)", "DIM"))
    for i, (bt, desc) in enumerate(fixes.BOARD_CHOICES, 1):
        mark = ui.c("  (detected)", "ACC") if bt == guess else ""
        print("    " + ui.c(str(i), "ACC") + "  " + desc + mark)
    hint = " (enter = detected) " if guess else " (enter = not sure) "
    raw = input("\n  " + ui.c("pick a number", "ACC")
                + ui.c(hint + "> ", "DIM")).strip()
    if not raw:
        chosen = guess or default
    elif raw.isdigit() and 1 <= int(raw) <= len(fixes.BOARD_CHOICES):
        chosen = fixes.BOARD_CHOICES[int(raw) - 1][0]
    else:
        chosen = default
    boards.remember_board_type(sig, chosen)  # never ask again
    return chosen


def mode_board(keyboard):
    """Re-pick and remember the keyboard type (clears the saved answer)."""
    ui.banner("set keyboard type")
    bt = _ask_board_type(force=True)
    desc = dict(fixes.BOARD_CHOICES).get(bt, bt)
    print("\n  " + ui.c(f"Saved: {desc}. KeySurgeon won't ask again.", "OK") + "\n")


def g_dot():
    return ui.g("+", "*")


def _show_verdict(verdict, board_type):
    rungs, closer = fixes.ladder_for(verdict["fault"], board_type)
    ui.card(verdict, rungs, closer)


# ---------- modes ----------

def mode_test(keys, expected, keyboard, board_type, save=True):
    keys = keys or EROW
    ui.banner(f"testing {len(keys)} key(s) - {expected} presses each")
    results = []
    hook = KeyboardHook().start()
    try:
        for k in keys:
            v = _run_one_key(hook, k, expected)
            if v:
                results.append(v)
                _show_verdict(v, board_type)
    except KeyboardInterrupt:
        print("\n  interrupted")
    finally:
        hook.stop()
    if results and save:
        profile.save_results(results, keyboard, board_type)
    return results


def mode_triage(expected, keyboard):
    ui.banner("let's find what's wrong")
    options = [
        ("A key types double or repeats", "chatter"),
        ("A key sometimes doesn't show up", "intermittent"),
        ("A key sticks or feels slow", "sticky"),
        ("The wrong letter comes out", "scancode"),
        ("Keys drop when I press several at once", "nkro"),
        ("Not sure - check the whole board", "sweep"),
        ("Just watch me type and tell me", "watch"),
    ]
    print("  " + ui.c("What's bugging you?", "BLD") + "\n")
    for i, (text, _) in enumerate(options, 1):
        print("    " + ui.c(str(i), "ACC") + "  " + text)
    raw = input("\n  " + ui.c("pick a number", "ACC") + ui.c(" > ", "DIM")).strip()
    if not raw.isdigit() or not (1 <= int(raw) <= len(options)):
        print("  " + ui.c("ok, never mind", "DIM"))
        return
    choice = options[int(raw) - 1][1]

    if choice == "sweep":
        return mode_sweep(expected, keyboard)
    if choice == "watch":
        return mode_watch(keyboard)
    if choice in ("scancode", "nkro"):
        print("\n  " + ui.c("That check isn't in this version yet - it's on the "
                            "roadmap.", "WRN"))
        print("  " + ui.c("For now, let's test the key directly.", "DIM"))

    keystr = input("\n  " + ui.c("Which key(s)? ", "ACC")
                   + ui.c("(e.g. E or  E W I) > ", "DIM")).strip()
    keys = keystr.split() if keystr else []
    if not keys:
        print("  " + ui.c("no keys given", "DIM"))
        return
    board_type = _ask_board_type()
    mode_test(keys, expected, keyboard, board_type)


def mode_fix(key, keyboard):
    if not key:
        key = input("  " + ui.c("Which key? ", "ACC") + ui.c("> ", "DIM")).strip()
    if not key:
        return
    label = key.upper()
    ui.banner(f"fix ladder for {label}")
    faultlist = [
        ("Double-typing / repeating", faults.CHATTER),
        ("Sometimes doesn't register", faults.INTERMITTENT),
        ("Completely dead", faults.DEAD),
        ("Sticks or feels mushy", faults.STICKY),
    ]
    print("  " + ui.c(f"What's {label} doing?", "BLD") + "\n")
    for i, (text, _) in enumerate(faultlist, 1):
        print("    " + ui.c(str(i), "ACC") + "  " + text)
    raw = input("\n  " + ui.c("pick a number", "ACC") + ui.c(" > ", "DIM")).strip()
    if not raw.isdigit() or not (1 <= int(raw) <= len(faultlist)):
        return
    fault = faultlist[int(raw) - 1][1]
    board_type = _ask_board_type()
    # build a minimal verdict so the card renders consistently
    verdict = {
        "fault": fault, "label": label,
        "headline": {
            faults.CHATTER: "This key is double-typing.",
            faults.INTERMITTENT: "This key skips sometimes.",
            faults.DEAD: "This key isn't responding.",
            faults.STICKY: "This key feels off.",
        }[fault],
        "detail": "Here's the cheapest-first way to fix it.",
        "evidence": [], "score": 35 if fault != faults.DEAD else 0,
        "confidence": "n/a",
    }
    _show_verdict(verdict, board_type)


def mode_report(keyboard):
    snap, board_type = profile.latest(keyboard)
    ui.report(snap, board_type or "unknown")


def mode_tour():
    import proof_report
    ui.tour(proof_report.build_payload())
    return 0


def mode_export(keyboard, args=None):
    args = args or []
    fmt = "md"
    out = None
    i = 0
    while i < len(args):
        if args[i] == "--json":
            fmt = "json"
        elif args[i] == "--md":
            fmt = "md"
        elif args[i] == "--out" and i + 1 < len(args):
            out = args[i + 1]
            i += 1
        i += 1
    import export_report
    text = export_report.render(keyboard, fmt)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print("  " + ui.c(f"export written: {out}", "OK"))
    else:
        print(text)


def mode_sweep(expected, keyboard):
    board_type = _ask_board_type()
    keys = [k for row in ["1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
            for k in row]
    ui.banner("full sweep - press each key as it's asked")
    print("  " + ui.c("Press each highlighted key until its counter fills. "
                      "ESC skips a key.", "DIM"))
    results = []
    hook = KeyboardHook().start()
    try:
        for k in keys:
            v = _run_one_key(hook, k, expected)
            if v:
                results.append(v)
    except KeyboardInterrupt:
        print("\n  interrupted")
    finally:
        hook.stop()
    if results:
        profile.save_results(results, keyboard, board_type)
        scores = {v["label"]: v["score"] for v in results}
        ui.heatmap(scores, "sweep results")
        snap, bt = profile.latest(keyboard)
        ui.report(snap, bt)


def mode_watch(keyboard, args=None):
    """Live chatter watch. Foreground by default; background via flags:
        watch            foreground, Ctrl+C to stop + summarize
        watch --bg       start a hidden background watcher
        watch --status   is it running? what has it caught?
        watch --stop     stop the background watcher
    """
    args = args or []
    if "--bg-run" in args:          # internal: the detached child process
        watch.bg_run(keyboard)
        return
    if "--status" in args:
        return _watch_status()
    if "--stop" in args:
        ok, msg = watch.stop_background()
        print("  " + ui.c(msg, "OK" if ok else "DIM"))
        return
    if "--bg" in args:
        ok, msg = watch.start_background(keyboard)
        print("  " + ui.c(msg, "OK" if ok else "BAD"))
        if ok:
            print("  " + ui.c("check on it with  keysurgeon watch --status", "DIM"))
        return

    # foreground
    ui.banner("watching for chatter - type normally, Ctrl+C when done")
    print("  " + ui.c("I'll flag any key that double-fires while you work.", "DIM"))
    print("  " + ui.c("Want it running all day? keysurgeon watch --bg "
                      "(then --status / --stop)", "DIM") + "\n")

    def on_bounce(name, gap, n, presses):
        print("  " + ui.c(g_flag(), "BAD") + ui.c(f" {name} bounced", "BAD")
              + ui.c(f"  ({gap}ms)  [{n} bounce{'s' if n != 1 else ''}, "
                     f"{presses} presses]", "DIM"))

    bounces, _presses = watch.run_loop(keyboard, on_bounce=on_bounce,
                                       write_state=False)
    if not bounces:
        print("\n  " + ui.c("No chatter seen. Keys look clean from how you type.",
                            "OK") + "\n")
        return
    scores = {vk_name(vk): 35 for vk in bounces}
    profile.save_results(
        [{"label": lbl, "fault": faults.CHATTER, "score": 35} for lbl in scores],
        keyboard, "unknown")
    ui.heatmap(scores, "chatter caught while typing")
    layout = set("1234567890QWERTYUIOPASDFGHJKLZXCVBNM")
    others = sorted(lbl for lbl in scores if lbl not in layout)
    if others:
        print("  " + ui.c("Also flagged (not on the map): ", "WRN")
              + ui.c(", ".join(others), "BAD") + "\n")
    print("  " + ui.c("Flagged keys are double-firing. Run "
                      "keysurgeon fix <key> for the repair ladder.", "ACC") + "\n")


def _watch_status():
    running, pid = watch.is_running()
    ui.banner("background watch status")
    if running:
        print("  " + ui.c(g_dot(), "OK") + ui.c(f" running (pid {pid})", "BLD"))
    else:
        print("  " + ui.c("not running", "DIM")
              + ui.c("  - start it with  keysurgeon watch --bg", "DIM"))
    state = watch.read_state()
    if not state or not state.get("keys"):
        print("  " + ui.c("no chatter caught yet", "DIM") + "\n")
        return
    print("  " + ui.c(f"watching since {state.get('started', '?')}, "
                      f"updated {state.get('updated', '?')}", "DIM") + "\n")
    print("  " + ui.c("Keys catching bounces:", "BLD"))
    for name, d in sorted(state["keys"].items(),
                          key=lambda kv: -kv[1]["bounces"]):
        print("    " + ui.c(f"{name:<6}", "BLD", "BAD")
              + ui.c(f"{d['bounces']} bounce{'s' if d['bounces'] != 1 else ''}"
                     f" in {d['presses']} presses", "DIM"))
    print()


def mode_site(args=None):
    args = args or []
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    path = root / "site" / "index.html"
    if not path.exists():
        print("  " + ui.c("local landing page is missing", "BAD"))
        print("  " + ui.c(str(path), "DIM"))
        return 1
    if getattr(sys, "frozen", False):
        target = Path(storage.path("landing-site"))
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(root / "site", target)
        path = target / "index.html"
    print("  " + ui.c("local landing page:", "BLD", "ACC"))
    print("  " + ui.c(str(path), "DIM"))
    print("  " + ui.c("public URL is not claimed until GitHub Pages passes.", "WRN"))
    if "--open" in args:
        webbrowser.open(path.as_uri())
        print("  " + ui.c("opened in your default browser", "OK"))
    return 0


def g_flag():
    return ui.g("!", "!")


# ---------- entry ----------

def _parse_flags(argv):
    opts = {"plain": False, "color": True, "glyphs": True,
            "keyboard": "default", "presses": 20}
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--plain", "--ai"):
            opts["plain"] = True
            opts["color"] = False
            opts["glyphs"] = False
        elif a == "--no-color":
            opts["color"] = False
        elif a == "--keyboard":
            if i + 1 < len(argv):
                opts["keyboard"] = argv[i + 1]
                i += 1
        elif a == "--presses":
            if i + 1 < len(argv):
                try:
                    opts["presses"] = int(argv[i + 1])
                except ValueError:
                    pass
                i += 1
        else:
            rest.append(a)
        i += 1
    return opts, rest


def _dispatch(mode, args, opts):
    kb = opts["keyboard"]
    n = opts["presses"]
    if mode in ("help", "-h", "--help"):
        print(HELP_TEXT)
        return 0
    elif mode in ("version", "--version"):
        print(VERSION)
        return 0
    elif mode == "app":
        import app_textual
        raise SystemExit(app_textual.run_app(kb))
    elif mode == "tour":
        return mode_tour()
    elif mode == "triage":
        mode_triage(n, kb)
        return 0
    elif mode == "sweep":
        mode_sweep(n, kb)
        return 0
    elif mode == "watch":
        mode_watch(kb, args)
        return 0
    elif mode == "test":
        mode_test(args, n, kb, _ask_board_type() if args else "unknown")
        return 0
    elif mode == "report":
        mode_report(kb)
        return 0
    elif mode == "issue":
        import issue_packet
        return issue_packet.run(args, kb)
    elif mode == "export":
        mode_export(kb, args)
        return 0
    elif mode == "proof":
        import proof_report
        return proof_report.run(args) or 0
    elif mode in ("site", "demo"):
        return mode_site(args)
    elif mode == "smoke":
        import manual_smoke
        return manual_smoke.run(args)
    elif mode == "fix":
        mode_fix(args[0] if args else None, kb)
        return 0
    elif mode == "board":
        mode_board(kb)
        return 0
    elif mode == "doctor":
        import doctor
        doctor.run()
        return 0
    elif mode == "selftest":  # maintenance: validate the logic, no keyboard needed
        import selftest
        return selftest.run()
    else:
        print("  " + ui.c(f"unknown mode '{mode}'", "BAD"))
        return 1


def main():
    opts, rest = _parse_flags(sys.argv[1:])
    ui.init(opts["color"], opts["glyphs"])

    if rest:  # a verb was given - jump straight to it
        return _dispatch(rest[0].lower(), rest[1:], opts)

    # no args -> menu loop
    valid = {num: mode for num, mode, *_ in ui.MENU_ITEMS}
    while True:
        choice = ui.menu().strip().lower()
        if choice in ("q", "quit", "exit"):
            print()
            return 0
        mode = valid.get(choice)
        if not mode:
            print("  " + ui.c("pick a listed number or q", "DIM"))
            continue
        _dispatch(mode, [], opts)
        input("\n  " + ui.c("press Enter for the menu", "DIM"))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n  bye")
        raise SystemExit(130)
