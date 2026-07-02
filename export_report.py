#!/usr/bin/env python3
"""Redacted evidence export for GitHub issues and repair notes."""

import json
import platform

import boards
import brand
import ks_profile as profile


def _summary(snapshot):
    keys = snapshot.get("keys") or []
    if not keys:
        return 100, []
    scores = [item.get("score", 0) for item in keys]
    avg = sum(scores) // len(scores)
    bad = sorted([item for item in keys if item.get("score", 0) < 90],
                 key=lambda item: item.get("score", 0))
    return avg, bad


def _device_lines():
    lines = []
    for item in boards.keyboards_only(boards.detect_keyboards()):
        name = item.get("product") or item.get("vendor") or "Keyboard"
        vid = item.get("vid") or "built-in"
        pid = item.get("pid") or ""
        hint = item.get("hint") or "type unknown"
        tail = f"VID {vid} PID {pid}" if pid else vid
        lines.append({
            "name": name,
            "id": tail,
            "hint": hint,
            "keys_total": item.get("keys_total"),
        })
    return lines


def build_payload(keyboard="default"):
    snap, board_type = profile.latest(keyboard)
    avg, bad = _summary(snap or {})
    return {
        "tool": brand.NAME,
        "version": brand.VERSION,
        "privacy": "No typed text is stored or exported. Key labels and timing-derived verdicts only.",
        "system": {
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "keyboard_profile": keyboard,
        "board_type": board_type or "unknown",
        "snapshot": {
            "timestamp": (snap or {}).get("ts"),
            "average_score": avg if snap else None,
            "keys_tested": len((snap or {}).get("keys") or []),
            "attention": [
                {
                    "label": item.get("label"),
                    "fault": item.get("fault"),
                    "score": item.get("score"),
                }
                for item in bad
            ],
        },
        "devices": _device_lines(),
    }


def to_markdown(payload):
    lines = [
        f"# {payload['tool']} Diagnostic Export",
        "",
        f"- Version: `{payload['version']}`",
        f"- Keyboard profile: `{payload['keyboard_profile']}`",
        f"- Board type: `{payload['board_type']}`",
        f"- Platform: `{payload['system']['platform']}`",
        f"- Python: `{payload['system']['python']}`",
        f"- Privacy: {payload['privacy']}",
        "",
        "## Latest Snapshot",
    ]
    snap = payload["snapshot"]
    if not snap["timestamp"]:
        lines.extend([
            "",
            "No saved diagnostic snapshot yet.",
            "",
            "Run `keysurgeon sweep` or `keysurgeon test <key>` first.",
        ])
    else:
        lines.extend([
            "",
            f"- Timestamp: `{snap['timestamp']}`",
            f"- Keys tested: `{snap['keys_tested']}`",
            f"- Average score: `{snap['average_score']}`",
        ])
        if snap["attention"]:
            lines.extend(["", "| Key | Fault | Score |", "|---|---|---:|"])
            for item in snap["attention"]:
                lines.append(
                    f"| `{item['label']}` | `{item['fault']}` | {item['score']} |"
                )
        else:
            lines.extend(["", "No saved keys need attention."])

    lines.extend(["", "## Detected Devices"])
    if payload["devices"]:
        for item in payload["devices"]:
            keys = item["keys_total"] if item["keys_total"] is not None else "unknown"
            lines.extend([
                "",
                f"- `{item['name']}`",
                f"  - ID: `{item['id']}`",
                f"  - Keys total: `{keys}`",
                f"  - Hint: {item['hint']}",
            ])
    else:
        lines.extend(["", "No keyboard identity was available from Windows Raw Input."])

    lines.extend([
        "",
        "## Reproduce",
        "",
        "```powershell",
        "keysurgeon doctor",
        "keysurgeon report",
        "keysurgeon export",
        "```",
        "",
    ])
    return "\n".join(lines)


def to_json(payload):
    return json.dumps(payload, indent=2)


def render(keyboard="default", fmt="md"):
    payload = build_payload(keyboard)
    if fmt == "json":
        return to_json(payload)
    return to_markdown(payload)
