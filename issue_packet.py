#!/usr/bin/env python3
"""GitHub-ready redacted issue packet."""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path

import brand
import export_report
import proof_report
import storage
import ui

PACKET_PUBLIC_PROMISE = "no typed text is stored or exported"
PACKET_CONTENTS = (
    "key labels, timing-derived verdicts, environment facts, asset proof, "
    "and readiness blockers"
)
PACKET_PRIVACY_WARNING = "Do not paste typed private text."
PACKET_REVIEW_WARNING = "review before posting; do not add typed private text."


def _default_packet_path() -> Path:
    return Path(storage.path("issue-packet")) / "KEYSURGEON_ISSUE_PACKET.md"


def _module_status(name: str) -> str:
    try:
        __import__(name)
        return "installed"
    except Exception:
        return "missing"


def _support_summary() -> str:
    """Allowlisted support facts only; no local filesystem paths."""
    return "\n".join([
        f"- Tool: `{brand.NAME} {brand.VERSION}`",
        f"- Platform: `{platform.system()} {platform.release()}`",
        f"- Python: `{platform.python_version()}`",
        f"- Rich: `{_module_status('rich')}`",
        f"- Textual: `{_module_status('textual')}`",
        f"- Runtime storage: `local user data dir, path redacted`",
        f"- Portable mode: `{'KEYSURGEON_HOME set' if os.environ.get('KEYSURGEON_HOME') else 'not set'}`",
    ])


def _fence(text: str, lang: str = "text") -> str:
    return f"```{lang}\n{text.strip()}\n```"


def build_packet(keyboard: str = "default") -> str:
    support_text = _support_summary()
    proof_text = json.dumps(proof_report.build_payload(), indent=2)
    export_text = export_report.render(keyboard, "json")
    return f"""# KeySurgeon Issue Packet

Paste this into a GitHub bug report or attach it with a short description of
what went wrong. It is designed for public issues: no typed text is stored or
exported, only key labels, timing-derived verdicts, environment facts, asset
proof, and readiness blockers.

## Summary To Fill In

- What command did you run?
- What did you expect?
- What happened instead?
- Keyboard brand/model:

## Version

`{brand.NAME} {brand.VERSION}`

## Support Summary

{support_text}

## Proof

{_fence(proof_text, "json")}

## Redacted Export

{_fence(export_text, "json")}

## Reproduce

```powershell
keysurgeon selftest
keysurgeon --plain doctor
keysurgeon proof --json
keysurgeon export --json
```

## Privacy Check

- {PACKET_PRIVACY_WARNING}
- KeySurgeon issue packets should contain only {PACKET_CONTENTS}.
"""


def run(args=None, keyboard: str = "default") -> int:
    args = args or []
    out = None
    i = 0
    while i < len(args):
        if args[i] == "--out" and i + 1 < len(args):
            out = Path(args[i + 1])
            i += 1
        i += 1
    path = out or _default_packet_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_packet(keyboard), encoding="utf-8")
    ui.banner("issue packet")
    print("  " + ui.c("redacted issue packet written:", "OK", "BLD"))
    print("  " + ui.c(str(path), "DIM"))
    print("  " + ui.c(PACKET_REVIEW_WARNING, "WRN"))
    return 0
