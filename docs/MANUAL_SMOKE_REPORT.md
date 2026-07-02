# Manual Smoke Report

Use this template after running `docs/MANUAL_KEYBOARD_SMOKE.md` on a real
Windows keyboard. Do not paste typed private text.

## Environment

- Date:
- Windows version:
- Python version:
- Install source: local checkout / GitHub install / executable artifact
- Keyboard brand/model:
- Keyboard type: hot-swap / soldered mechanical / membrane / laptop / unknown

## Commands Run

```powershell
keysurgeon --version
keysurgeon selftest
keysurgeon --plain doctor
keysurgeon test E
keysurgeon watch --bg
keysurgeon watch --status
keysurgeon watch --stop
keysurgeon watch --status
```

## Results

| Check | Pass/Fail | Evidence |
|---|---|---|
| Version prints expected release |  |  |
| Selftest passes |  |  |
| Doctor reports environment |  |  |
| `test E` captures the key label |  |  |
| `test E` exits with a readable verdict |  |  |
| Watch background starts |  |  |
| Watch status reports state |  |  |
| Watch stop stops the recorded PID |  |  |
| Runtime JSON stays under expected data dir |  |  |
| No typed private text is stored |  |  |

## Chatter Evidence

Only fill this section if a known chattering key or controlled repeat input was
tested.

- Key label:
- Verdict:
- Score:
- Timing evidence:
- Repair ladder shown:

## Release Claim

Choose one:

- `hardware-smoke-pass`: hook path and watcher behavior passed on a real
  keyboard.
- `hardware-smoke-partial`: some behavior passed, but gaps remain.
- `hardware-smoke-fail`: do not claim real hardware behavior yet.

Notes:
