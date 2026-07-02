# First Issues

Use these starter issues after the public repository exists. They are scoped to
work KeySurgeon can already verify locally, and they avoid unsupported claims
about latency certification, remapping, macros, or broad hardware proof.

For copy/paste issue bodies, use `docs/STARTER_ISSUE_TEMPLATES.md`.

Apply `good first issue` to small tasks with a clear done state. Apply
`help wanted` when outside board facts, install evidence, repair wording, tests,
or manual smoke evidence would materially improve the release.

## Board Data

Title:

```text
[board-data]: add repair hints for <brand model>
```

Good evidence:

- Brand and exact model.
- Laptop or external keyboard.
- Mechanical, membrane, hot-swap, or soldered if known.
- Vendor page, manual, teardown note, or a clear user report.
- Non-private KeySurgeon output from `keysurgeon export --json` if available.

Done when:

- `boards.py` contains the new conservative hint.
- The hint does not overpromise hot-swap, soldering, or replacement steps.
- `python keysurgeon.py selftest` passes.

## Repair Ladder Wording

Title:

```text
[docs]: clarify first repair step for <fault or board type>
```

Good evidence:

- The current confusing sentence or command output.
- The keyboard type involved.
- The safer replacement wording.

Done when:

- The wording still follows the cheapest-first ladder:
  software filter, debris, contact clean, hot-swap, solder, replace.
- It does not claim live repair actions or guaranteed hardware recovery.
- `python keysurgeon.py selftest` passes.

## Install Friction

Title:

```text
[docs]: improve Windows install note for <shell or Python setup>
```

Good evidence:

- Windows version.
- Shell used: PowerShell, Windows Terminal, cmd, or other.
- `python --version` output.
- Exact non-private install error.

Done when:

- `README.md` or `docs/DIAGNOSIS_GUIDE.md` gives a clearer fix path.
- The note preserves the current local-checkout install flow until GitHub is
  actually published.
- `.\scripts\verify-public-tree.ps1` passes.

## Test Coverage

Title:

```text
[test]: cover <fault, export, proof, or UI state>
```

Good evidence:

- The behavior that should stay stable.
- A small synthetic sample or existing function path.

Done when:

- The test uses synthetic events or local state only.
- No typed private text is added to fixtures, logs, docs, or screenshots.
- `python keysurgeon.py selftest` passes.

## Not Starter Scope

Do not use starter issues for:

- Global key remapping.
- Macro layers.
- NKRO or rollover certification.
- Latency benchmarking.
- Cloud sync or telemetry.
- Claims that require a real keyboard smoke pass unless the issue is only to
  record that manual smoke evidence.
