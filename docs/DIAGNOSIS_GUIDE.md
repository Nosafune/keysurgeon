# Diagnosis Guide

KeySurgeon reports a verdict, a confidence signal, and the cheapest honest
repair path. Read the top line first, then use the evidence lines to decide
whether to retest, clean, swap, or replace.

## Verdicts

| Verdict | What it means | First move |
|---|---|---|
| `HEALTHY` | The tested key behaved normally during this run. | No repair needed. |
| `WATCH` | The key is suspicious but not proven bad yet. | Retest or run `keysurgeon watch`. |
| `DEGRADING` | The key missed, repeated, or released oddly often enough to act. | Clean or isolate the switch. |
| `FAILING` | The key showed a repeatable fault. | Follow the repair ladder for that key. |

Scores are not keyboard value judgments. They are a compact summary of the
current evidence for one key or one saved board snapshot.

## Faults

| Fault | Signal KeySurgeon is looking for |
|---|---|
| `chatter` | One physical press produces fast repeated events. |
| `dead` | A requested key does not register during the test window. |
| `intermittent` | The key registers sometimes and misses sometimes. |
| `sticky` | Hold or release timing looks wrong. |
| `extra` | Late bounces appear after the expected press/release pattern. |

## Evidence Lines

- `re-press 31ms`: a second event arrived too quickly to be a normal intentional
  press.
- `18 bounces in 240 presses`: repeated chatter was seen across the sample.
- `hold`: the key stayed active long enough to affect the score.
- `confidence`: how strongly the observed timing supports the verdict.

## When To Retest

Retest before buying parts if the result came from only one quick sample, if the
key was pressed unevenly, if a macro layer was active, or if another tool was
also listening for hotkeys. Run `keysurgeon doctor` when the terminal output or
environment looks wrong.

## Compatibility

KeySurgeon is built for Windows terminal use. The Rich interface is the default,
the Textual command center is available with `keysurgeon app`, and `--plain` or
`--no-color` keeps output suitable for logs, automation, and simple terminals.

## Sharing Evidence

Run `keysurgeon export` after `keysurgeon test`, `keysurgeon sweep`, or
`keysurgeon watch --status` when you need to file a GitHub issue or keep repair
notes. The export is intentionally redacted: it includes key labels, verdicts,
scores, platform, board type, and device identity, but not typed private text.
Run `keysurgeon proof --json` with public reports too. It summarizes local asset
proof, redacted readiness status, and the remaining blockers without including
typed private text.

```powershell
keysurgeon proof --json
keysurgeon smoke --out MANUAL_SMOKE_REPORT.md
keysurgeon export --out keysurgeon-report.md
keysurgeon export --json
```

Manual keyboard behavior still needs a real keyboard smoke test before a release
claim says hardware behavior is proven. `keysurgeon smoke` only creates the
safe scaffold; the interactive table must still be completed on real hardware.
