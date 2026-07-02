# KeySurgeon — Design & Build Plan

> A smart, guided keyboard diagnostic that finds **fixable** problems before
> you throw the board away. Diagnose → explain → prescribe a fix ladder that
> climbs from "free software filter" up to "replace the switch", and only ever
> ends at "replace the board" when nothing cheaper will work.

Status: **v0.1 BUILT (2026-06-14).** M0–M6 shipped + device auto-detect; passed
a 37-agent adversarial review (19 bugs found & fixed). Untested by hand on real
chatter (needs a physical keyboard session). This doc is the living contract.

Home: `C:\AIDIR\TOOLS\keysurgeon`
Builds on: [`keytest`](../keytest/keytest.py) (trial engine) and
[`chatterguard`](../chatterguard/chatterguard.py) (live debounce filter).
Stack: Python 3, Windows-only (ctypes `WH_KEYBOARD_LL`). Rich powers the
default terminal UI, Textual powers optional `keysurgeon app`, and the
diagnostic core keeps a plain/no-color fallback for automation.

---

## Verdict — is this worth building?

**Yes.** Not as a hedge — here's the actual argument:

Every keyboard tester on the market does one thing: lights up a key when it
registers. They prove a key *works*. **None of them catch chatter** — the single
most common way a mechanical board dies — because to a dumb tester a chattering
key looks fine; it registers. It just registers *twice*. KeySurgeon does the
timing math that exposes that. That's a real, unfilled gap.

The soul is the **honest fix ladder**: a tool whose answer is usually "don't buy
a new board, here's the $0.30 fix." Everything else in this space nudges you
toward replacement. This nudges you toward repair. That's worth making.

The standout feature is `watch` — *"type normally for a day, I'll tell you what's
dying."* Nobody does that.

**Where this could go wrong, so we don't let it:** scope creep into things that
can't be measured honestly (latency without a hardware reference) or that serve
a tiny audience (NKRO). Those are **cut from v1** (§3b). The discipline is: a
ruthless core done well — chatter/dead/intermittent/sticky detection, the fix
ladder, a clean heatmap, and `watch` — beats a feature checklist that never
ships. Build that, and it doesn't suck.

---

## 1. The core idea

Most people's mental model is binary: *keyboard works* or *keyboard is broken,
buy a new one*. The truth is a **ladder of fixes**, and most failures get
resolved well before the top:

```
0. Software debounce filter      free, instant        (chatter)
1. Compressed-air / debris blow  free, 1 min          (dead/sticky/grit)
2. Keycap pull + contact clean   free, 5 min          (sticky/intermittent)
3. Switch reseat / re-solder     skill, 15 min        (intermittent on solder boards)
4. Hot-swap single switch        ~$0.30, 2 min        (chatter/dead on hotswap boards)
5. Desolder + replace switch     skill+iron, 20 min   (chatter/dead on soldered boards)
6. Replace the keyboard          $$$                  (controller dead, spill rot, PCB trace gone)
```

KeySurgeon's job: **detect the fault, identify which rung the user can reach,
and walk them up it.** The win condition is "fixed it for free or for cents."

---

## 2. Problem taxonomy — everything a keyboard can do wrong

Each fault has: how we **detect** it, whether it's **fixable**, and the **fix rung**.

| Fault | Symptom | How KeySurgeon detects | Fixable? | Fix rungs |
|---|---|---|---|---|
| **Chatter / bounce** | one press → 2+ chars | re-press <35ms after release (keytest CHATTER) | **Yes** | 0 → 4/5 |
| **Dead key** | press → nothing | trial never registers (STALLED) | **Often** | 1 → 2 → 4/5 |
| **Intermittent / flaky** | works 8/10 times | registered < expected, no chatter | **Often** | 1 → 2 → 3 |
| **Sticky key** | char repeats / slow release | abnormally long holds, EXTRA bounces | **Often** | 1 → 2 (lube/spring) |
| **Slow / mushy actuation** | feels laggy, missed fast presses | short-hold misses at speed | sometimes | 2 (clean/lube) |
| **Ghosting / blocking** | combos drop keys | NKRO matrix test (press groups) | **No** (inherent) | identify only; informs gamers |
| **Stuck-down key** | key fires forever | down with no up for >Ns | **Yes** | 1 → 2 |
| **Wrong scancode / mismapped** | wrong char appears | scancode ≠ expected vk | **Yes** (software) | remap |
| **Modifier stuck/flaky** | random CAPS, stuck Shift/Ctrl | modifier-specific trial | **Often** | 1 → 2 → 4/5 |
| **Connection dropout** | whole board cuts out | gap in event stream / device reset | maybe | cable/port/battery |
| **Worn legends** | can't read keycap | n/a (cosmetic) | cosmetic | keycaps only |
| **Spill / corrosion** | multiple adjacent dead | cluster of dead keys in a region | rarely | 6 (usually) |

The taxonomy is the heart of the **recommendation engine** (§6). New faults =
new rows = new data, not new control flow (same philosophy as NULLDIVER's
"new content = data").

---

## 3. Diagnostic battery

Reusable test primitives. keytest already has the first two; the rest are new.

1. **Chatter trial** *(have)* — N presses/key, flag re-press <35ms. → chatter.
2. **Registration trial** *(have)* — did all N register? → dead / intermittent.
3. **Hold-consistency trial** *(extend)* — median hold + variance + short-hold
   misses. → sticky / mushy / slow actuation.
4. **Stuck-key watch** *(new)* — flag any key held >2s with no release. → stuck.
5. **Scancode audit** *(new)* — record scancode per key, compare to expected
   layout. → mismapping / wrong-key.
6. **NKRO / ghosting test** *(new)* — prompt user to hold key groups (e.g.
   W+A+S+D, then +Space, +Shift), count how many register at once. → rollover
   limit (diagnostic only; not fixable, but worth knowing).
7. **Passive monitor** *(new, big one)* — run quietly during the user's *real*
   typing; build a per-key health profile from natural use. Surfaces failing
   keys **without** a manual trial. This is the "smart" differentiator — most
   tools make you test every key; KeySurgeon notices on its own.
8. **Modifier trial** *(new)* — dedicated Shift/Ctrl/Alt/Win L+R tests
   (chatter on modifiers is sneaky and common).

Each primitive returns a structured result `{key, test, metrics, verdict,
confidence}`. The engine consumes verdicts; the UI renders them.

---

## 3b. Modes — one clean verb each

KeySurgeon has exactly **six modes**. You never have to remember a verb: running
`keysurgeon` with **no args opens a menu** listing every mode — pick a number.
The verbs are just shortcuts for when you *do* remember. Menu-first, verbs
optional.

```
  KeySurgeon · pick a mode

    1  Triage    something's wrong — walk me through it
    2  Sweep     check the whole board (live heatmap)
    3  Watch     run in the background, tell me what's dying
    4  Test      test specific keys right now
    5  Report    how's my board doing? (last results + trend)
    6  Fix       show the fix ladder for one key

    q  quit

  pick a number ›
```

| Command | Mode | What it does | Who it's for |
|---|---|---|---|
| `keysurgeon` | **menu** *(default)* | the picker above — no verb needed | you, who forgets commands |
| `keysurgeon triage` | **triage** | "What's bugging you?" wizard → targeted test → fix ladder | anyone, the front door |
| `keysurgeon sweep` | **sweep** | walk the whole board, fill the live heatmap, end on a board report | "check everything" |
| `keysurgeon watch` | **watch** | run quietly in the background while you type for real; build a health profile and flag dying keys on its own | the standout — set and forget |
| `keysurgeon test E R T` | **test** | power-user: run trials on named keys right now, no wizard | you, fast |
| `keysurgeon report` | **report** | show the latest profile, board health, and trend — no testing | "how's my board doing?" |
| `keysurgeon fix E` | **fix** | jump straight to the fix ladder for one key | you already know what's wrong |

Cross-cutting flags (work on any mode): `--plain`/`--ai` (no-ANSI structured
out), `--no-color`, `--keyboard <name>` (pick the device profile).

**Scope discipline (my recommendation, not yet locked):** `triage`, `sweep`,
`test`, `report`, `fix` are v1. `watch` is the headline and should be v1 too if
the budget holds — it's the differentiator. Latency timing, NKRO, and scancode
audit are **explicitly cut from v1**: latency can't be measured honestly without
a hardware reference, NKRO is gamer-niche, scancode audit is rare. They become
optional sub-checks later, never a reason to delay shipping the core.

---

## 4. The guided flow (this is what makes it "guided")

Two entry modes — a wizard for "something's wrong", a sweep for "check
everything".

### A. Triage wizard (default)
```
What's bugging you?
  1) A key types double / repeats        → Chatter trial on suspect keys
  2) A key sometimes doesn't type        → Registration + intermittent trial
  3) A key sticks or feels slow          → Hold-consistency + stuck watch
  4) Wrong character comes out           → Scancode audit
  5) Keys drop when I press several       → NKRO test
  6) I don't know / check the whole thing → Full sweep
  7) Just watch me type and tell me      → Passive monitor
```
Each branch: ask which key(s) → run the matching trial → show verdict →
**hand off to the recommendation engine** (§6) → offer to apply/queue the fix.

### B. Full sweep
Walk the whole board region by region (function row → number row → QWERTY rows →
modifiers → arrows/nav → numpad). Live keyboard map (§7) fills in as each key
clears. Ends with a board health report + prioritized fix list.

### Smart routing
The wizard isn't a dumb menu — once a trial confirms a fault, KeySurgeon
**auto-suggests adjacent checks** ("E chatters — bounce often spreads; want me
to quick-check W, R, D, S too?"). Encodes the real-world pattern that switch
failures cluster.

---

## 5. Health scoring

Per-key score 0–100 and a board roll-up, so degradation is trackable over time.

- Start 100. Subtract by severity: chatter −40, dead −100, intermittent
  −(miss% ×), sticky −30, short-holds −10, etc.
- **Confidence** field: a verdict from 8 manual presses is low-confidence; one
  from 500 passively-observed presses is high. Surface both.
- Persist profiles to `keysurgeon_profile.json` keyed by **device** (so a laptop
  board vs the BlackWidow track separately). Each run appends a timestamped
  snapshot → **trend view**: "E was 95 last week, 60 now — accelerating."
- Board verdict: HEALTHY / WATCH / DEGRADING / FAILING, with the worst keys
  named and their fix rung.

---

## 6. Recommendation engine — the payoff

Input: a verdict + key + board metadata (hotswap? soldered? laptop?
membrane/mechanical?). Output: an ordered, **honest** fix ladder with effort,
cost, and reversibility per rung — and an explicit "don't replace the board
yet, try X first."

Example (E chatters, mechanical hotswap board):
```
KEY E — CHATTER (re-press 31ms, switch is bouncing). Confidence: HIGH (240 presses)

This is a failing switch, not your fault. Fix ladder:
  ✓ 0  Software filter      chatterguard already blocks <45ms bounces — running?
    1  Blow it out          compressed air under the cap; debris can mimic chatter
    4  Hot-swap the switch  pull cap+switch, drop a new one in (~$0.30, 2 min)
                            your board IS hotswap → this is the real fix
  ✗ 6  Replace keyboard     NOT NEEDED for a single chattering switch

Recommended: run chatterguard now (free, instant), order a switch, hot-swap when it arrives.
```

Board metadata is asked **once** (or remembered per device): *Is this a laptop
or external? Mechanical or membrane? If mechanical, hot-swap or soldered?* That
single fact reshapes the whole ladder (a laptop scissor switch ≠ a hotswap MX).

The engine is **data-driven**: a `fixes` table mapping `(fault, board_type) →
ordered rungs`. Adding boards/faults later = data edits.

---

## 7. Terminal UI

Match Joey's house style: chocolate-orange accent, green OK, red fail, amber
warn (same palette as keytest). Nerd Font glyphs with ASCII fallback.

### Voice & feel — the hard rule

KeySurgeon **talks like a person who knows keyboards**, not like a log file.
This is a first-class requirement, not polish.

- **No raw error codes.** Never `ERR 1733 SEE LOG`. Say what happened in plain
  words: *"E is double-firing — the switch is bouncing."*
- **Plain-language verdict first, numbers in support.** The headline is human
  ("This key is double-typing"); the metrics (`re-press 31ms`) live underneath
  as evidence, dimmed, for people who want them.
- **Always say what it means for the user**, not just what was measured. Not
  "regap 31ms < 35" → instead "that's a failing switch, not your typing."
- **Reassure + direct.** Every fault ends with a clear, ranked *do this next*.
  Never leave the user at a dead end.
- **Calm, not alarmist.** Red means "needs a fix," not "panic." Confident keys
  get a quiet green check, not a parade.
- **One idea per line.** Short lines, generous spacing, no wall-of-text dumps.

A verbose `--log` / `chatterguard.log`-style file can still exist for the curious
— but the *interface* never makes you read a log to understand what's wrong.

### Screens (mockups — design target, not final art)

**Live keyboard heatmap** (sweep + passive). Each key tinted by health; legend
below; the eye finds the red cluster instantly:

```
  KeySurgeon · board health while you type

   Esc   F1 F2 F3 F4   F5 F6 F7 F8   F9 F10 F11 F12

   `  1  2  3  4  5  6  7  8  9  0  -  =  ⌫
   ⇥  Q  W  E  R  T  Y  U  I  O  P  [  ]  \
   ⇪  A  S  D  F  G  H  J  K  L  ;  '  ⏎
   ⇧  Z  X  C  V  B  N  M  ,  .  /  ⇧
                ␣

   ● healthy   ● watch   ● degrading   ● failing      (E, I failing · W watch)
```
(In the real thing E/I render red, W amber, everything else green — color does
the work; the parenthetical names are the fallback for no-color terminals.)

**Per-key card** — human headline, evidence dimmed below, ranked fix:

```
  ┌─ E ───────────────────────────────── FAILING ─┐
  │                                                │
  │  This key is double-typing.                    │
  │  The switch is bouncing — that's hardware      │
  │  wear, not anything you're doing wrong.        │
  │                                                │
  │  evidence · re-press 31ms (human floor ~60ms)  │
  │           · 18 bounces in 240 presses          │
  │           · confidence: high                   │
  │                                                │
  │  What to do, easiest first:                    │
  │    1  Software filter — blocks the bounce now,  │
  │       free. Good stopgap.                       │
  │    2  Blow it out — debris can mimic this.      │
  │    3  Hot-swap the switch — ~$0.30, 2 min.      │
  │       Your board supports it. This is the fix.  │
  │                                                │
  │  You do NOT need a new keyboard for this.       │
  └────────────────────────────────────────────────┘
```

**Triage open** — friendly, plain options (the §4 wizard):

```
  KeySurgeon · let's find what's wrong

  What's bugging you?

    1  A key types double or repeats
    2  A key sometimes doesn't show up
    3  A key sticks or feels slow
    4  The wrong letter comes out
    5  Keys drop when I press several at once
    6  Not sure — check the whole board
    7  Just watch me type and tell me

  pick a number ›
```

- **Report screen**: board score, ranked problem keys, the single most important
  next action up top — phrased as a sentence, not a table dump.
- `--ai` / `--plain` flag: plain-text, no ANSI, machine-readable summary — per
  Joey's CLI convention so output can be piped without dumping escape codes.
  This is the *one* place terse/structured output is correct.

---

## 8. Architecture

```
keysurgeon/
  keysurgeon.py        # CLI entry, arg parsing, mode dispatch
  hook.py              # shared WH_KEYBOARD_LL hook + event pump (lifted from
                       #   keytest/chatterguard — single source of truth)
  trials.py            # diagnostic primitives (§3), each returns a verdict
  faults.py            # taxonomy table (§2) — data
  fixes.py             # recommendation ladders (§6) — data
  scoring.py           # health math + board roll-up (§5)
  ks_profile.py        # load/save/trend keysurgeon_profile.json, per-device
  ui.py                # ANSI render: keyboard map, cards, report, --plain path
  wizard.py            # guided triage flow (§4)
```

**Reuse, don't fork:** the low-level ctypes hook is currently duplicated across
keytest and chatterguard. KeySurgeon's `hook.py` becomes the canonical version;
later we can point the old two at it (optional cleanup, not required).

**Device identity:** use `GetRawInputDeviceInfo` to get the device handle/name
so profiles separate the laptop board from the BlackWidow. (Stretch — fall back
to a manual "which keyboard is this?" prompt if raw-input device id is fiddly.)

---

## 9. Build phases

| Phase | Deliverable | Status |
|---|---|---|
| **M0** | `hook.py` shared hook + event model (perf_counter timing) | ✅ done |
| **M1** | `trials.py` chatter/registration/hold trial | ✅ done |
| **M2** | `faults.py` classify+score, `fixes.py` board-aware ladders | ✅ done |
| **M3** | triage wizard + per-key cards (in `keysurgeon.py`/`ui.py`) | ✅ done |
| **M4** | live keyboard heatmap + full sweep + report | ✅ done |
| **M5** | `ks_profile.py` persistence + trend | ✅ done |
| **M6** | `watch` live chatter monitor (foreground **+ detached background**) | ✅ done |
| **+** | `boards.py` USB auto-detect + vendor knowledge base | ✅ done (bonus) |
| **M7** | launcher + README + registry + CLAUDE.md | 🔜 launcher+README done |
| ~~Mx~~ | ~~latency / NKRO / scancode audit~~ | **cut from v1** — see §3b |

Remaining for v1 polish: register in PROJECT_REGISTRY, optional PS alias,
hand-test on a real chattering key. Deferred: detached background `watch`
(pythonw + pid like chatterguard), per-model PID database, scancode/NKRO checks.
Anything that can't be measured honestly stays cut, not faked.

---

## 10. Decisions

**Locked (2026-06-14):**
- ✅ **Name** — KeySurgeon.
- ✅ **v1 scope** — M0–M4. The keyboard heatmap ships in v1, not later.
- ✅ **Voice** — human, plain-language, no error codes. First-class requirement
  (see §7 "Voice & feel").

- ✅ **Passive monitor (M6)** — built (foreground `watch`).
- ✅ **Device detection** — built; raw-input VID auto-detect with manual confirm
  for hot-swap/soldered (not VID-knowable). Verified live: detects Razer (1532).

- ✅ **Detached `watch`** — built (`watch.py`): `--bg` / `--status` / `--stop`,
  pythonw+pid, live state file + periodic profile save. Mirrors chatterguard.

**Still open:**
1. **chatterguard**: fold its live-filter into KeySurgeon as the "apply fix
   rung 0" action, or keep it standalone and just point at it?
   *(currently: points at it - the filter rung names chatterguard.)*
2. **Audience**: just your boards, or built to hand to other people?
3. **Per-model PID database**: map specific PIDs → exact model + hot-swap flag so
   it can stop asking even for hot-swap/soldered (needs a curated DB).
4. **scancode audit / NKRO** — still cut (niche / not honestly measurable as
   wired today); revisit only if a real need shows up.

---

## 11. Known pitfalls (from FAILINGS.md)

- **Don't block the shell** with any long-running watch/monitor mode — passive
  monitor must run detached (pythonw + pid file, like chatterguard), never
  inline in a terminal.
- **Never kill by process name** — if a monitor needs stopping, use the pid file
  + verified PID (chatterguard's `--stop` pattern is correct, reuse it).
- **No nested quote-escaping** across launchers — AIDIR paths are space-free,
  pass args bare.
- **Keep a `--plain`/`--ai` path** — never force ANSI into a pipe.
- ctypes 64-bit: keep the explicit `argtypes`/`restype` prototypes (both
  existing tools have them — pointers get truncated without).

---

## 12. Open question — bigger picture

Is KeySurgeon a **CLI** (fits your terminal-kit world, fastest to build) or
eventually a **small GUI/tray app** (friendlier if you ever hand it out)? The
architecture above is CLI-first but the engine/data layers (faults, fixes,
scoring, trials) are UI-agnostic on purpose — a GUI could sit on the same brain
later. Recommend: **build CLI-first, keep the brain UI-free.**
