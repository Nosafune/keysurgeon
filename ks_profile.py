#!/usr/bin/env python3
"""Profile persistence for KeySurgeon.

Saves trial results so `report` can show board health and trend over time.
Stored in the user's KeySurgeon data directory. Per-keyboard by name so a
laptop board and an external board track separately.
"""

import json
import time

import storage

PROFILE = storage.path("keysurgeon_profile.json")


def _load_raw():
    try:
        with open(PROFILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"keyboards": {}}


def save_results(verdicts, keyboard="default", board_type="unknown"):
    """Append a timestamped snapshot for one keyboard.
    verdicts: list of dicts from faults.classify()."""
    data = _load_raw()
    kbs = data.setdefault("keyboards", {})
    kb = kbs.setdefault(keyboard, {"board_type": board_type, "snapshots": []})
    kb["board_type"] = board_type
    kb["snapshots"].append({
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "keys": [
            {"label": v["label"], "fault": v["fault"], "score": v["score"]}
            for v in verdicts
        ],
    })
    # keep last 50 snapshots per keyboard
    kb["snapshots"] = kb["snapshots"][-50:]
    try:
        with open(PROFILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


def latest(keyboard="default"):
    """Return (snapshot, board_type) for the most recent run, or (None, None).
    Degrades to (None, None) on structurally malformed (but valid-JSON) data."""
    kb = _load_raw().get("keyboards", {}).get(keyboard)
    if not isinstance(kb, dict):
        return None, None
    snaps = kb.get("snapshots") or []
    if not snaps:
        return None, None
    return snaps[-1], kb.get("board_type", "unknown")


def trend(keyboard="default", label=None):
    """Return [(ts, score)] history for one key label, oldest first."""
    kb = _load_raw().get("keyboards", {}).get(keyboard)
    if not isinstance(kb, dict):
        return []
    out = []
    for snap in kb.get("snapshots") or []:
        for k in snap.get("keys") or []:
            if k.get("label") == label:
                out.append((snap.get("ts", "?"), k.get("score", 0)))
    return out


def keyboards():
    return list(_load_raw().get("keyboards", {}).keys())
