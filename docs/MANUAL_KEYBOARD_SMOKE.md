# Manual Keyboard Smoke

This verifies the real Windows keyboard hook path. Synthetic selftests do not
prove hardware behavior.

## Setup

Use a Windows machine with Python 3.10+ and a keyboard you can safely test.
Close applications where accidental typing matters.

```powershell
python -m pip install .
keysurgeon --version
keysurgeon selftest
```

## Basic Hook Smoke

1. Run `keysurgeon test E`.
2. Press `E` the requested number of times at a normal pace.
3. Confirm the command ends with a readable verdict and does not hang.
4. Repeat with at least one modifier key if prompted by the current CLI flow.

Pass criteria:

- Key labels are captured correctly.
- The app exits cleanly.
- No typed private text is stored in runtime JSON.

## Watch Smoke

```powershell
keysurgeon watch --bg
keysurgeon watch --status
keysurgeon watch --stop
keysurgeon watch --status
```

Pass criteria:

- `--bg` starts a background watcher.
- `--status` reports the watcher state.
- `--stop` stops only the recorded watcher PID.
- Runtime files are under `%LOCALAPPDATA%\KeySurgeon` unless `KEYSURGEON_HOME`
  is set.

## Chatter Proof

The public claim "catches chatter ordinary testers miss" is fully proven only
after one of these:

- test a known chattering key and capture the verdict, or
- use a controlled input rig that produces repeat presses under the chatter
  threshold.

Do not claim real chatter proof from `selftest` alone.

## Evidence Record

Use the CLI helper to create a report scaffold from a checkout, pip install, or
executable artifact:

```powershell
keysurgeon smoke --out docs\MANUAL_SMOKE_REPORT.md
```

For a source checkout, the PowerShell helper can also create a report scaffold
with safe non-interactive checks:

```powershell
.\scripts\manual-keyboard-smoke.ps1
```

Then run the interactive commands printed in the generated report on a real
keyboard. Neither helper proves hardware behavior by itself.

Record the run in `docs/MANUAL_SMOKE_REPORT.md`. Keep it to command output,
key labels, timing evidence, verdicts, environment facts, and keyboard model
details. Do not paste typed private text.

Before recording `hardware-smoke-pass`, check that the report is filled enough
from any install shape:

```powershell
keysurgeon smoke --check docs\MANUAL_SMOKE_REPORT.md
```

The check is read-only. It rejects blank result cells, the install-source
placeholder, missing keyboard identity, and missing `hardware-smoke-pass` claim.

After the real-keyboard run is complete, update `docs/MANUAL_SMOKE_RESULT.md`.
Broad real-hardware claims stay off the table until that file records
`hardware-smoke-pass`.

Use the recorder so the gate file stays in the expected format:

```powershell
.\scripts\record-manual-smoke-result.ps1 -Result hardware-smoke-pass -EvidenceReport docs\MANUAL_SMOKE_REPORT.md -Tester "name" -Keyboard "brand model" -InstallSource "local checkout"
```

Use `hardware-smoke-partial` or `hardware-smoke-fail` instead of pass if any
required check is missing or failed. The recorder refuses `hardware-smoke-pass`
unless an evidence report path is provided, exists, includes keyboard identity,
replaces the install-source placeholder, fills the results table, and records
`hardware-smoke-pass`.
