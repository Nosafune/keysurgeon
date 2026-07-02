#!/usr/bin/env python3
"""KeySurgeon self-test - validates the brain without needing a keyboard.

The live hook/trials need real keypresses, but everything downstream (fault
classification, scoring, fix ladders, persistence, board detection, watch state)
is pure logic and IS testable. Run this after any edit:

    python keysurgeon.py selftest      (or:  python selftest.py)

Exits non-zero on the first failure. stdlib only, no test framework.
"""

import contextlib
import io
import os
import tempfile
from pathlib import Path

import app_textual
import boards
import export_report
import faults
import fixes
import issue_packet
import keysurgeon
import ks_profile as profile
import manual_smoke
import proof_report
import trials
import watch

_fails = []


def check(name, cond):
    mark = "ok " if cond else "FAIL"
    print(f"  [{mark}] {name}")
    if not cond:
        _fails.append(name)


def _stats(label, **kw):
    base = {"label": label, "vk": 0, "expected": 20, "registered": 20,
            "chatter": 0, "min_regap": None, "short_holds": 0,
            "med_hold": 40, "max_hold": 60}
    base.update(kw)
    return base


class _FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class _ReplayHook:
    def __init__(self, events):
        self._pending = list(events)
        self.events = []

    def pump(self):
        if self._pending:
            self.events.append(self._pending.pop(0))


def run():
    print("\n  KeySurgeon self-test\n")

    # --- classification: every fault path lands on the right fault ---
    cases = {
        faults.CHATTER: _stats("E", chatter=18, min_regap=31),
        faults.DEAD: _stats("Q", registered=0),
        faults.INTERMITTENT: _stats("W", registered=14),
        faults.EXTRA: _stats("I", registered=23),
        faults.STICKY: _stats("T", short_holds=4, med_hold=5),
        faults.OK: _stats("A"),
    }
    for want, st in cases.items():
        got = faults.classify(st)["fault"]
        check(f"classify -> {want}", got == want)

    # --- scoring sanity: chatter scales, intermittent doesn't saturate ---
    light = faults.classify(_stats("E", expected=200, registered=200, chatter=1))
    heavy = faults.classify(_stats("E", expected=60, registered=60, chatter=50))
    check("chatter score scales with rate", light["score"] > heavy["score"])
    mid = faults.classify(_stats("W", expected=100, registered=50))
    sev = faults.classify(_stats("W", expected=100, registered=10))
    check("intermittent score not saturated", mid["score"] > sev["score"])
    check("OK scores 100", faults.classify(_stats("A"))["score"] == 100)
    check("band(0)==FAILING", faults.band(0) == "FAILING")
    check("band(100)==HEALTHY", faults.band(100) == "HEALTHY")

    # --- trial replay: raw hook events become timing stats, no hardware needed ---
    orig_time = trials.time
    try:
        trials.time = _FakeClock()
        replay = _ReplayHook([
            (69, True, 0),
            (69, False, 40),
            (69, True, 71),    # 31ms after release: chatter
            (69, False, 110),
            (69, True, 200),
            (69, False, 245),
        ])
        st = trials.chatter_trial(replay, 69, "E", 3)
        check("trial replay registers expected presses", st["registered"] == 3)
        check("trial replay detects chatter timing",
              st["chatter"] == 1 and st["min_regap"] == 31)
        check("trial replay preserves hold timing",
              st["med_hold"] == 40 and st["max_hold"] == 45)
        check("trial replay classifies chatter",
              faults.classify(st)["fault"] == faults.CHATTER)
    finally:
        trials.time = orig_time

    # --- fix ladders: board-aware filtering + honesty ---
    hot, _ = fixes.ladder_for(faults.CHATTER, fixes.HOTSWAP)
    hot_titles = [t for _, t, _ in hot]
    check("hotswap chatter offers hot-swap", "Hot-swap the switch" in hot_titles)
    check("hotswap chatter hides desolder",
          "Desolder + replace the switch" not in hot_titles)
    mem, _ = fixes.ladder_for(faults.CHATTER, fixes.MEMBRANE)
    mem_titles = [t for _, t, _ in mem]
    check("membrane chatter has a clean rung before replace",
          "Clean the contact" in mem_titles)
    check("replace is always last",
          mem_titles[-1] == "Replace the keyboard")
    stick, _ = fixes.ladder_for(faults.STICKY, fixes.HOTSWAP)
    check("sticky on hotswap offers swap",
          "Hot-swap the switch" in [t for _, t, _ in stick])
    ok_rungs, _ = fixes.ladder_for(faults.OK, fixes.UNKNOWN)
    check("OK fault -> no ladder", ok_rungs == [])

    # --- persistence: round-trip + malformed-JSON resilience ---
    orig = profile.PROFILE
    fd, tmp = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        profile.PROFILE = tmp
        profile.save_results(
            [{"label": "E", "fault": faults.CHATTER, "score": 35}],
            "selftest-kb", "hotswap")
        snap, bt = profile.latest("selftest-kb")
        check("profile round-trip", snap and snap["keys"][0]["label"] == "E")
        check("profile keeps board type", bt == "hotswap")
        check("profile trend", profile.trend("selftest-kb", "E") != [])
        with open(tmp, "w", encoding="utf-8") as f:
            f.write('{"keyboards": {"selftest-kb": {"board_type": "x"}}}')  # no snapshots
        check("malformed profile degrades, no crash",
              profile.latest("selftest-kb") == (None, None))
    finally:
        profile.PROFILE = orig
        try:
            os.remove(tmp)
        except OSError:
            pass

    # --- board detection: best-effort, never raises, returns a list ---
    det = boards.detect_keyboards()
    check("detect_keyboards returns a list", isinstance(det, list))
    check("best_guess_type handles empty", boards.best_guess_type([]) is None)

    # --- device role + model inference ---
    check("mouse filtered by product name",
          boards._looks_like_mouse("Razer Mamba Elite", 264) is True)
    check("real keyboard not filtered",
          boards._looks_like_mouse("Razer BlackWidow V4 Pro", 264) is False)
    check("low key count flags non-keyboard",
          boards._looks_like_mouse("", 6) is True)
    check("known model -> board type",
          boards.infer_from_model("Razer BlackWidow V4 Pro") == "soldered")
    check("hotswap model recognized",
          boards.infer_from_model("Keychron Q1") == "hotswap")
    check("unknown model -> None",
          boards.infer_from_model("Mystery Board 9000") is None)
    check("keyboards_only drops mice",
          boards.keyboards_only(
              [{"role": "other"}, {"role": "keyboard"}]) ==
          [{"role": "keyboard"}])

    # --- board-type memory: ask once, remember, recall, forget ---
    orig_bt = boards.BOARDTYPES
    fd, tmp = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        boards.BOARDTYPES = tmp
        sig = boards.device_signature([{"vid": "1532", "pid": "006C"}])
        check("device signature stable", sig == "1532:006C")
        check("recall before save -> None", boards.recall_board_type(sig) is None)
        boards.remember_board_type(sig, "hotswap")
        check("recall after remember", boards.recall_board_type(sig) == "hotswap")
        boards.forget_board_type(sig)
        check("forget clears it", boards.recall_board_type(sig) is None)
    finally:
        boards.BOARDTYPES = orig_bt
        try:
            os.remove(tmp)
        except OSError:
            pass

    # --- watch state: atomic round-trip ---
    orig_state = watch.STATEFILE
    fd, tmp = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        watch.STATEFILE = tmp
        watch._write_state("k", "t0", {69: 2}, {69: 100})
        s = watch.read_state()
        check("watch state round-trip",
              s and s["keys"]["E"]["bounces"] == 2)
        signal = app_textual._signal_text(None)
        check("textual signal uses watch state",
              "E" in signal and "2 bounce(s)" in signal)
        check("textual signal avoids fake trace",
              "__|_|" not in signal and "watch mode listens" not in signal)
        rail = app_textual._signal_rail({"keys": [
            {"label": "E", "fault": faults.CHATTER, "score": 35},
            {"label": "Q", "fault": faults.OK, "score": 100},
        ]})
        check("textual signal rail uses saved and live evidence",
              "chatter" in rail and "2 hit(s)" in rail and "67/100" in rail)
        check("textual signal rail avoids fake metrics",
              "proof" in rail and "__|_|" not in rail and "fake" not in rail.lower())
        hero = app_textual._hero_text({"keys": [
            {"label": "Q", "fault": faults.OK, "score": 100},
        ]})
        check("textual hero prefers live watch evidence",
              "E" in hero and "bouncing live" in hero and "Q" not in hero)
    finally:
        watch.STATEFILE = orig_state
        try:
            os.remove(tmp)
        except OSError:
            pass

    # --- Textual command center: routes to real CLI/watch flows, no fake actions ---
    orig_is_running = app_textual.watch.is_running
    orig_read_state = app_textual.watch.read_state
    try:
        app_textual.watch.is_running = lambda: (False, None)
        app_textual.watch.read_state = lambda: None
        empty_hero = app_textual._hero_text(None)
        check("textual hero starts with honest empty state",
              "no active evidence yet" in empty_hero and
              "Auto-updates every 3s" in empty_hero)
        empty_center = app_textual._command_center(None)
        check("textual command center starts with watch or sweep",
              "press w to arm background watch" in empty_center and
              "keysurgeon sweep" in empty_center)
        check("textual command center exposes proof command",
              "keysurgeon proof --json" in empty_center)
        ready_out = io.StringIO()
        with contextlib.redirect_stdout(ready_out):
            keysurgeon._dispatch("ready", [], {"keyboard": "default", "presses": 20})
        ready_text = ready_out.getvalue()
        check("ready command shows local launch board",
              "Local proof:" in ready_text and "Next safe actions:" in ready_text)
        check("ready command is no-mutation",
              "no git, GitHub, release, Pages, or deploy changes" in ready_text)
        saved_center = app_textual._command_center({
            "keys": [{"label": "Q", "fault": faults.CHATTER, "score": 35}]
        })
        check("textual command center uses weakest saved key",
              "keysurgeon fix Q" in saved_center)
        saved_hero = app_textual._hero_text({
            "keys": [{"label": "Q", "fault": faults.CHATTER, "score": 35}]
        })
        check("textual hero uses weakest saved key",
              "Q" in saved_hero and "saved fault" in saved_hero)
        app_textual.watch.read_state = lambda: {
            "keys": {"E": {"bounces": 3, "presses": 20}}
        }
        live_center = app_textual._command_center(None)
        check("textual command center uses live watch key",
              "keysurgeon fix E" in live_center and "keysurgeon test E" in live_center)
        orig_latest = app_textual.profile.latest
        try:
            app_textual.profile.latest = lambda keyboard: (None, None)
            unknown_device = app_textual._device_text("default")
            app_textual.profile.latest = lambda keyboard: (None, "hotswap")
            saved_device = app_textual._device_text("default")
            check("textual device panel exposes board repair context",
                  "repair model:" in unknown_device and
                  "unknown" in unknown_device and
                  "keysurgeon board" in unknown_device and
                  "hotswap" in saved_device and
                  "saved for this profile" in saved_device)
        finally:
            app_textual.profile.latest = orig_latest
        check("textual CLI flow exposes proof command",
              "KEYS" in app_textual._commands() and
              "CLI FLOW" in app_textual._commands() and
              "keysurgeon proof --json" in app_textual._commands())
        actions = app_textual._action_bar()
        binding_keys = [item[0] for item in app_textual._app_bindings()]
        action_keys = [item["key"] for item in app_textual.APP_ACTIONS]
        check("textual action bar exposes only real safe commands",
              "ACTION BAR" in actions and
              "keysurgeon board" in actions and
              "keysurgeon issue" in actions and
              "keysurgeon proof --json" in actions and
              "keysurgeon site --open" in actions and
              "No fake repair buttons" in actions and
              "No typed text exported" in actions and
              binding_keys == action_keys and
              all(item["safe"] for item in app_textual.APP_ACTIONS))
        issue_panel = app_textual._issue_packet_text()
        check("textual issue packet panel explains redacted GitHub packet",
              "ISSUE PACKET" in issue_panel and
              f"keysurgeon issue --out {issue_packet._default_packet_path().name}" in issue_panel and
              "support summary" in issue_panel and
              "proof JSON" in issue_panel and
              "redacted export" in issue_panel and
              issue_packet.PACKET_PUBLIC_PROMISE in issue_panel and
              issue_packet.PACKET_CONTENTS in issue_panel and
              issue_packet.PACKET_REVIEW_WARNING in issue_panel)
        readiness = app_textual._readiness_text({
            "local_proof": {
                "demo_assets": {
                    "status": "ok",
                    "detail": "generated demo assets match recorded hashes",
                    "assets": [{"path": "site/assets/keysurgeon-demo.svg"}],
                },
                "manual_keyboard_smoke": {
                    "status": "blocked",
                    "detail": "real keyboard smoke is not run",
                },
                "rich_textual_stack": {
                    "status": "ok",
                    "detail": "Rich/Textual public demos are hash-verified",
                },
                "package_build_gate": {
                    "status": "command-gated",
                    "detail": "wheel/package build proof is produced by scripts/release-check.ps1",
                    "command": "scripts/release-check.ps1",
                },
                "package_metadata": {
                    "status": "ok",
                    "detail": "pyproject search metadata includes 17 keywords and planned GitHub URLs",
                    "keywords": ["keyboard", "repair"],
                    "urls": {"Repository": "https://github.com/nosafune/keysurgeon"},
                },
                "proof_matrix": {
                    "status": "ok",
                    "detail": "docs/PROOF_MATRIX.md maps local-ready, command-gated, and blocked public claims",
                    "claims": 2,
                },
                "release_package": {
                    "status": "blocked",
                    "detail": "local release package proof is not built",
                },
            },
            "proof_summary": {
                "local": 1,
                "command_gated": 0,
                "blocked": 1,
            },
            "public_blockers": [
                "manual keyboard smoke must record hardware-smoke-pass",
                "GitHub repository and remote workflow proof must exist",
            ],
            "next_actions": [
                {"command": ".\\scripts\\release-packet.ps1", "changes_remote": False},
                {"command": ".\\scripts\\release-commit-plan.ps1", "changes_remote": False},
            ],
        })
        check("textual readiness panel shows proof blockers",
              "READINESS" in readiness and
              "assets:" in readiness and
              "hardware:" in readiness and
              "package:" in readiness and
              "metadata:" in readiness and
              "claims:" in readiness and
              "release:" in readiness and
              "blocked:" in readiness and
              "GitHub repository" in readiness and
              "next:" in readiness and
              ".\\scripts\\release-packet.ps1" in readiness)
        check("textual readiness panel avoids fake ready state",
              "no public blockers reported" not in readiness)
        ladder = app_textual._repair_ladder()
        check("textual repair ladder remains available in app shell",
              "REPAIR LADDER" in ladder and
              "replace keyboard" in ladder and
              "last resort" in ladder)
    finally:
        app_textual.watch.is_running = orig_is_running
        app_textual.watch.read_state = orig_read_state

    # --- redacted export: issue-ready evidence, no typed text ---
    orig_profile = export_report.profile.PROFILE
    fd, tmp = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        export_report.profile.PROFILE = tmp
        export_report.profile.save_results(
            [{"label": "E", "fault": faults.CHATTER, "score": 35}],
            "export-kb", "hotswap")
        md = export_report.render("export-kb", "md")
        js = export_report.render("export-kb", "json")
        check("export markdown includes redacted fault evidence",
              "KeySurgeon Diagnostic Export" in md and
              "| `E` | `chatter` | 35 |" in md)
        check("export json includes privacy statement",
              "No typed text is stored or exported" in js)
        check("export omits private prose fields",
              "typed private text" not in md.lower())
        issue_text = issue_packet.build_packet("export-kb")
        check("issue packet includes proof and redacted export",
              "KeySurgeon Issue Packet" in issue_text and
              "## Support Summary" in issue_text and
              "## Proof" in issue_text and
              "## Redacted Export" in issue_text and
              "keysurgeon proof --json" in issue_text)
        check("issue packet keeps privacy warning",
              "Do not paste typed private text" in issue_text and
              "typed private text from user" not in issue_text.lower() and
              "C:\\Users\\" not in issue_text and
              "AppData" not in issue_text)
    finally:
        export_report.profile.PROFILE = orig_profile
        try:
            os.remove(tmp)
        except OSError:
            pass

    # --- local landing page command: discoverable without browser side effects ---
    check("site command reports local landing page",
          keysurgeon.mode_site([]) == 0)
    check("site command target exists",
          Path("site/index.html").exists())
    tour_out = io.StringIO()
    with contextlib.redirect_stdout(tour_out):
        tour_code = keysurgeon._dispatch(
            "tour", [], {"keyboard": "default", "presses": 1})
    tour_text = tour_out.getvalue()
    check("tour command shows honest command center",
          tour_code == 0 and
          "first-run tour" in tour_text and
          "keysurgeon watch --bg" in tour_text and
          "keysurgeon proof --json" in tour_text and
          "keysurgeon issue" in tour_text and
          "Not claimed yet" in tour_text)
    unknown_out = io.StringIO()
    with contextlib.redirect_stdout(unknown_out):
        unknown_code = keysurgeon._dispatch(
            "__unknown__", [], {"keyboard": "default", "presses": 1})
    check("unknown CLI mode returns failure", unknown_code == 1)
    smoke_text = manual_smoke.build_report()
    check("manual smoke scaffold names interactive requirement",
          "does not prove hardware behavior" in smoke_text and
          "keysurgeon test E" in smoke_text and
          "hardware-smoke-pass" in smoke_text)
    blank_report = Path(".runtime/selftest-blank-manual-smoke.md")
    blank_report.parent.mkdir(parents=True, exist_ok=True)
    blank_report.write_text(smoke_text, encoding="utf-8")
    check("manual smoke CLI check rejects blank scaffold",
          manual_smoke.validation_errors(blank_report) and
          manual_smoke.check_report(blank_report) == 1)
    whitespace_report = smoke_text.replace(
        "| Version prints expected release |  |  |",
        "| Version prints expected release |    |    |",
    )
    whitespace_path = Path(".runtime/selftest-whitespace-manual-smoke.md")
    whitespace_path.write_text(whitespace_report, encoding="utf-8")
    check("manual smoke CLI check rejects whitespace-only cells",
          any("blank Pass/Fail" in error for error in manual_smoke.validation_errors(whitespace_path)))
    complete_report = smoke_text.replace(
        "Install source: local checkout / GitHub install / executable artifact",
        "Install source: local checkout",
    ).replace(
        "Keyboard brand/model:\n- Keyboard type:",
        "Keyboard brand/model: Test Board 1000\n- Keyboard type:",
    ).replace(
        "| Version prints expected release |  |  |",
        "| Version prints expected release | Pass | 0.2.0 printed |",
    ).replace(
        "| Selftest passes |  |  |",
        "| Selftest passes | Pass | all checks passed |",
    ).replace(
        "| Doctor reports environment |  |  |",
        "| Doctor reports environment | Pass | doctor passed |",
    ).replace(
        "| `test E` captures the key label |  |  |",
        "| `test E` captures the key label | Pass | E captured |",
    ).replace(
        "| `test E` exits with a readable verdict |  |  |",
        "| `test E` exits with a readable verdict | Pass | readable verdict shown |",
    ).replace(
        "| Watch background starts |  |  |",
        "| Watch background starts | Pass | PID recorded |",
    ).replace(
        "| Watch status reports state |  |  |",
        "| Watch status reports state | Pass | state printed |",
    ).replace(
        "| Watch stop stops the recorded PID |  |  |",
        "| Watch stop stops the recorded PID | Pass | stopped recorded PID |",
    ).replace(
        "| Runtime JSON stays under expected data dir |  |  |",
        "| Runtime JSON stays under expected data dir | Pass | LOCALAPPDATA KeySurgeon |",
    ).replace(
        "| No typed private text is stored |  |  |",
        "| No typed private text is stored | Pass | labels and timing only |",
    )
    complete_report += "\nRelease result: hardware-smoke-pass\n"
    complete_path = Path(".runtime/selftest-complete-manual-smoke.md")
    complete_path.write_text(complete_report, encoding="utf-8")
    check("manual smoke CLI check accepts completed report",
          not manual_smoke.validation_errors(complete_path) and
          manual_smoke.check_report(complete_path) == 0)

    # --- local proof report: demo provenance + honest public blockers ---
    proof = proof_report.build_payload()
    check("proof report includes demo asset proof",
          proof["local_proof"]["demo_assets"]["status"] == "ok")
    check("proof report preserves manual smoke blocker",
          proof["local_proof"]["manual_keyboard_smoke"]["status"] != "ok")
    check("proof report exposes release package gate",
          proof["local_proof"]["release_package"]["status"] in {"ok", "blocked", "stale"})
    check("proof report separates package build gate",
          proof["local_proof"]["package_build_gate"]["status"] in {"command-gated", "missing"} and
          proof["local_proof"]["package_build_gate"]["command"] == "scripts/release-check.ps1")
    check("proof report exposes package metadata",
          proof["local_proof"]["package_metadata"]["status"] == "ok" and
          "repair" in proof["local_proof"]["package_metadata"]["keywords"] and
          "Repository" in proof["local_proof"]["package_metadata"]["urls"])
    matrix_doc = Path("docs/PROOF_MATRIX.md").read_text(encoding="utf-8")
    parsed_claims = [item["claim"] for item in proof["proof_matrix"]]
    check("proof report exposes proof matrix",
          proof["local_proof"]["proof_matrix"]["status"] == "ok" and
          proof["proof_summary"]["blocked"] >= 1 and
          "Public GitHub repository exists" in parsed_claims)
    check("proof matrix tracks documented claims",
          all(f"| {claim} |" in matrix_doc for claim in parsed_claims))
    check("proof report names remote blockers",
          "GitHub repository" in proof["public_blockers"][1])
    check("proof report exposes next release moves",
          proof["next_actions"][0]["command"] == ".\\scripts\\release-packet.ps1" and
          all(action["changes_remote"] is False for action in proof["next_actions"]))

    render_app = Path("scripts/render-app-svg.py").read_text(encoding="utf-8")
    render_manifest = Path("scripts/render-proof-manifest.py").read_text(encoding="utf-8")
    check("app demo renderer includes readiness and ladder panels",
          "_readiness_text" in render_app and "_repair_ladder" in render_app and
          "_action_bar" in render_app and "_issue_packet_text" in render_app and
          "_device_text" in render_app and "_commands" in render_app)
    check("proof manifest names current app panels",
          "readiness, repair ladder" in render_manifest and
          "fake readiness" in render_manifest)

    print()
    if _fails:
        print(f"  {len(_fails)} FAILED: {', '.join(_fails)}\n")
        return 1
    print("  all checks passed\n")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(run())
