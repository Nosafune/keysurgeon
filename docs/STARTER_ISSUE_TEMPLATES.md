# Starter Issue Templates

Use these after the public repository exists and issue intake is enabled. They
are maintainer-seeded issues, not claims that public proof already exists.

Before posting, replace bracketed text, keep private typed text out, and remove
any evidence line that is not available.

For a local dry-run command packet, run:

```powershell
.\scripts\seed-starter-issues-plan.ps1 -AsMarkdown
```

The script prints `gh issue create` commands only. Do not run those commands
until the repository exists, labels exist, and issue intake is enabled.

## Board Data

Title:

```text
[board-data]: add conservative repair hint for [brand model]
```

Body:

```markdown
## What this improves

KeySurgeon can give a better repair ladder when it recognizes this board model.

## Evidence to add

- Brand/model:
- External, laptop, or unknown:
- Mechanical, membrane, or unknown:
- Hot-swap, soldered, or unknown:
- VID/PID if available:
- Source for the board facts:

## Guardrails

- Do not infer hot-swap support from USB vendor ID alone.
- If the source is weak, use a conservative hint and keep asking the user to confirm.
- Do not add typed private text, screenshots of typed text, or telemetry.

## Done

- `boards.py` contains the conservative board hint.
- `python keysurgeon.py selftest` passes.
- The hint does not overpromise repairability.
```

Labels:

```text
board-data
good first issue
help wanted
```

## Install Friction

Title:

```text
[docs]: clarify Windows install path for [PowerShell/cmd/Python setup]
```

Body:

```markdown
## Problem

A Windows install path is confusing or fails before the first `keysurgeon selftest`.

## Evidence

- Windows version:
- Shell:
- Python command used:
- `python --version`:
- Non-private error text:

## Desired outcome

The README or diagnosis guide should make the next command obvious without
claiming the future GitHub install path works before publish.

## Done

- The install note preserves the current local-checkout path.
- `.\scripts\verify-public-tree.ps1` passes.
- No private paths, tokens, or typed text are added.
```

Labels:

```text
enhancement
good first issue
help wanted
```

## Repair Ladder Wording

Title:

```text
[docs]: make the [fault] repair ladder clearer for [board type]
```

Body:

```markdown
## Confusing wording

Quote the current sentence or output line that is unclear.

## Better wording

Suggest a plain-language replacement that keeps replacement as the last rung.

## Context

- Fault:
- Board type:
- Why the current wording could mislead someone:

## Done

- The wording is cheapest-first: software filter, debris, contact clean,
  switch work, replacement last.
- It does not promise a repair KeySurgeon cannot apply itself.
- `python keysurgeon.py selftest` passes.
```

Labels:

```text
enhancement
good first issue
```

## Test Coverage

Title:

```text
[test]: cover [fault/export/proof/UI state]
```

Body:

```markdown
## Behavior to lock down

Describe the small behavior that should not regress.

## Suggested proof

- Synthetic event sample, saved profile state, or parser case:
- Expected verdict/output:

## Done

- The test uses synthetic events or local sample state.
- No real typed text is added to fixtures or logs.
- `python keysurgeon.py selftest` passes.
```

Labels:

```text
enhancement
good first issue
```

## Manual Hardware Smoke Evidence

Title:

```text
[hardware-smoke]: record real keyboard smoke for [artifact/install path]
```

Body:

```markdown
## Scope

Record real Windows keyboard evidence for one install path or release artifact.
This issue should not claim broad hardware proof until the linked smoke result
is complete.

## Evidence

- Install source:
- Keyboard brand/model:
- Tester:
- Date:
- Commands run:
  - `keysurgeon selftest`
  - `keysurgeon doctor`
  - `keysurgeon test [key]`
  - `keysurgeon smoke`
- Result file or report:

## Done

- `docs/MANUAL_SMOKE_RESULT.md` records `hardware-smoke-pass` only after the
  real interactive test passes.
- Private typed text is not included.
- `.\scripts\pre-publish-audit.ps1` no longer blocks on manual hardware smoke.
```

Labels:

```text
hardware-smoke
help wanted
```

## Not Appropriate For Starter Issues

- Global remapping or macro systems.
- NKRO certification.
- Latency benchmarking without hardware reference equipment.
- Cloud sync, telemetry, or account features.
- Claims that GitHub Actions, Pages, releases, or executable downloads exist
  before those remote surfaces actually pass.
