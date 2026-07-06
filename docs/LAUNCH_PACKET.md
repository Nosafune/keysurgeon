# Launch Packet

Use this copy after the public repository exists, local verification passes, and
the publish gate audit reports the remaining remote state honestly. Replace
repository URLs only after they resolve.

## One-Line Pitch

KeySurgeon is a Windows terminal diagnostic that catches keyboard chatter and
turns the evidence into a cheapest-first repair path.

## Repository Sidebar

Description:

```text
Keyboard chatter diagnostic for Windows: catch double-typing, dead keys, and
repair-first faults in a Rich/Textual terminal app.
```

Topics:

```text
keyboard
keyboard-tester
keyboard-diagnostics
keyboard-chatter
keyboard-repair
double-typing
dead-keys
debounce
mechanical-keyboard
usb-hid
hardware-diagnostics
windows
cli
rich
textual
repair
```

## Short Launch Post

```text
I built KeySurgeon, a Windows terminal diagnostic for keyboard chatter.

Most keyboard testers only show whether a key registers. KeySurgeon looks at
timing, flags double-fires, and gives a repair ladder before replacement:
software filter -> clean -> hot-swap -> solder -> replace.

It has a Rich terminal UI, optional Textual command center, plain output for logs,
local-only runtime files, and a selftest/doctor path for support.

Repo: https://github.com/nosafune/keysurgeon
```

## Keyboard Tester Angle

```text
If a keyboard tester says the key works but it still double-types, the missing
signal is timing. KeySurgeon checks for chatter, missed presses, sticky behavior,
and repair steps before replacement.

Comparison: https://github.com/nosafune/keysurgeon/blob/main/docs/KEYBOARD_TESTER_COMPARISON.md
```

## First-Run Copy

```text
Try the local loop:

python -m pip install .
keysurgeon selftest
keysurgeon tour
keysurgeon test E
keysurgeon fix E
keysurgeon ready
keysurgeon proof --json

The useful part is not just the verdict. KeySurgeon turns the timing evidence
into a repair decision: watch, clean, isolate the switch, hot-swap, solder, or
replace only as the last rung.
```

## Longer Release Copy

```text
KeySurgeon helps answer a specific hardware question: is this key actually
failing, and what should I try before buying another keyboard?

It is aimed at double-typing, missed keys, sticky behavior, and intermittent
switch faults. The default CLI uses Rich for readable diagnostic cards, while
`keysurgeon app` opens a Textual command center. `--plain` and `--no-color` remain
available for logs and automation.

The project is privacy-conservative: it uses timing and key labels for
diagnostics, does not store typed text, and does not send telemetry. Runtime
JSON stays under the local user data folder unless `KEYSURGEON_HOME` is set.

For support, `keysurgeon export` produces a redacted Markdown report with
version, platform, device identity, key labels, verdicts, and scores. It does
not export typed private text.
```

## Screenshot Caption

```text
KeySurgeon catches a chattering E key and shows the evidence plus the cheapest
repair path before replacement.
```

## Launch Rules

- Do not claim a GitHub release, executable, Pages homepage, or green CI until
  the matching remote proof exists.
- Do not claim broad hardware proof until `docs/MANUAL_KEYBOARD_SMOKE.md` has
  been run on a real keyboard.
- Prefer the repository README as the first destination until Pages passes.
- Use `docs/PROOF_MATRIX.md` when asked which claims are locally proven versus
  still blocked by hardware, GitHub, Pages, workflow, or release evidence.
- Use the keyboard-tester comparison link when posting in places where people
  are already searching for dead-key or double-typing checks.
- Use `docs/STARTER_ISSUE_TEMPLATES.md` to seed a few public issues after
  repository setup so early traffic has obvious contribution paths.
- Use `.\scripts\seed-starter-issues-plan.ps1 -AsMarkdown` to generate a
  dry-run command packet before running any `gh issue create` command.
- Use `site/assets/keysurgeon-social.png` for social preview and
  `site/assets/keysurgeon-landing-desktop.png` for the primary screenshot after
  running `.\scripts\generate-demo-assets.ps1`; the same command regenerates the
  headless landing screenshots, workflow demo, Rich diagnosis demo SVG/PNG,
  app signal-rail demo SVG/PNG, and proof manifest. The terminal demo PNGs are
  rasterized captures of verified demo renderers with Windows Terminal-style
  framing, not live interactive terminal screenshots. Run
  `python .\scripts\verify-textual-app.py` or `.\scripts\verify-public-tree.ps1`
  to prove the Textual app also mounts headlessly and its core bindings work.
- The landing page has Open Graph, Twitter card, and JSON-LD metadata with
  repository, issue tracker, platform, and screenshot fields, but no canonical
  public URL or `og:url` should be added until Pages resolves.
- Use `.\scripts\release-packet.ps1` to create a local dry-run review folder
  with the current audit JSON, commit plan, GitHub setup plan, starter issue
  plan, proof JSON, launch-readiness board, post-publish audit JSON, asset
  proof, and launch copy. The packet is not publish proof; it preserves the
  same blocker language as `pre-publish-audit.ps1`.
- After the repository and release exist, run `.\scripts\post-publish-audit.ps1`
  before claiming public visibility, starter issues, Pages, or download proof.
- Use `.\scripts\launch-readiness.ps1 -AsMarkdown` when you only need the
  current launch board without generating the full release packet.
