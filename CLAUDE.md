# KeySurgeon — agent notes

Guided keyboard diagnostic. Finds **fixable** faults before replacing the board.
Full design: `DESIGN.md`. Usage: `README.md`. Read those before editing; this is
just the router + guardrails.

## What it is
Python 3, **Windows only** (ctypes `WH_KEYBOARD_LL`). Rich owns the default
terminal skin, Textual owns optional `app` mode, and `--plain` / `--no-color`
keep the automation-safe fallback. Menu-first CLI, modes: triage / sweep /
watch / test / report / fix / app. Grew from
`../keytest`; the "software filter" fix rung points at `../chatterguard`.

## Module map
- `keysurgeon.py` — entry, menu, mode dispatch, board-type prompt
- `hook.py` — shared low-level keyboard hook (single source of truth)
- `trials.py` — diagnostic trial primitives
- `faults.py` — fault classification + 0-100 health scoring
- `fixes.py` — board-aware fix ladders (data)
- `boards.py` — Raw Input USB auto-detect + vendor knowledge base
- `ks_profile.py` — per-keyboard result history + trend (`keysurgeon_profile.json`)
- `brand.py` — Forensic Signal color, mark, and version tokens
- `rich_ui.py` — Rich renderer for cards, heatmap, report, and menu
- `app_textual.py` — optional Textual command-center shell with signal rail
- `ui.py` — rendering switchboard; `--plain`/`--no-color` fallback

## Hard rules (don't regress these — all came from review)
- **Timing uses `time.perf_counter()` captured in the hook callback, NOT
  `kb.time`.** The message tick is ~10-16ms and wraps every 49.7 days — useless
  for 5-35ms bounce. Never revert to kb.time for gap/hold math.
- **Honesty over false precision.** Don't assert what you can't measure: latency
  needs a hardware reference (cut), and hot-swap vs soldered isn't knowable from
  USB VID (so `boards.py` hints and asks, never guesses).
- **Human voice.** Verdict headline is plain English; numbers are dimmed
  evidence; every fault ends with a ranked "what to do" and never a raw error
  code. See DESIGN §7.
- Keep explicit ctypes `argtypes`/`restype` (64-bit pointer safety).
- Detection is best-effort: `boards.detect_keyboards()` must return `[]` on any
  failure, never raise.

## Validate after editing
Run `python keysurgeon.py selftest` (or `python selftest.py`) — 24 checks over
classification, scoring, fix ladders, persistence, board detect, and watch
state. No keyboard needed. Add a check when you add behavior. The live
hook/trials still need a real keypress session to verify.

## Status
v0.1, committed on `feat/mirror-rift`. Passed a 37-agent adversarial review
(19 bugs fixed) + targeted reviews of boards.py and watch.py. Self-test green.
**Not yet hand-tested on a real chattering key.**
