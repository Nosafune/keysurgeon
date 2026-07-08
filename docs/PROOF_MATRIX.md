# Proof Matrix

This keeps public claims tied to local evidence: what's actually verified
right now, and what's still blocked pending real proof.

## Local Proof

| Claim | Proof command or file | Current status |
|---|---|---|
| Fault classification and selftest logic work | `python keysurgeon.py selftest` | Proven locally with synthetic hook replay. |
| Export avoids typed private text | `python keysurgeon.py selftest` and `python keysurgeon.py export --json` | Proven locally by redacted export checks. |
| Demo assets match their real source code | `site/assets/keysurgeon-proof.json` and `scripts/verify-proof-manifest.py` | Proven locally by hash-verified provenance. |
| Textual command center is wired | `python scripts/verify-textual-app.py` | Proven locally by a headless mount and action smoke. |
| Wheel builds cleanly | `.\scripts\release-check.ps1` | Command-gated local proof. |

## Blocked Until Required Proof Exists

| Claim | Required proof | Why blocked |
|---|---|---|
| Broad real-keyboard hardware behavior | `docs/MANUAL_SMOKE_RESULT.md` records `hardware-smoke-pass` after the `docs/MANUAL_KEYBOARD_SMOKE.md` flow | Requires an interactive real Windows keyboard run. |

## Reporting Rule

Use local proof language until the matching evidence exists:

- `local-ready` for source, assets, and package checks that pass locally.
- `command-gated` for proofs that are produced and cleaned by release scripts.
- `blocked` for hardware and other claims that still need real evidence.
