#!/usr/bin/env python3
"""Local proof/readiness report for public KeySurgeon claims."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import brand
import ui


ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
MANIFEST = ROOT / "site" / "assets" / "keysurgeon-proof.json"
MANUAL_SMOKE = ROOT / "docs" / "MANUAL_SMOKE_RESULT.md"
PROOF_MATRIX = ROOT / "docs" / "PROOF_MATRIX.md"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_status():
    if not MANIFEST.exists():
        return {
            "status": "missing",
            "detail": "site/assets/keysurgeon-proof.json is missing",
            "assets": [],
        }
    proof = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = []
    stale = []
    for item in proof.get("assets") or []:
        path = ROOT / item["path"]
        if not path.exists():
            assets.append({**item, "status": "missing"})
            stale.append(item["path"])
            continue
        live_bytes = path.stat().st_size
        live_hash = _sha256(path)
        ok = live_bytes == item["bytes"] and live_hash == item["sha256"]
        assets.append({
            "path": item["path"],
            "kind": item.get("kind"),
            "generator": item.get("generator"),
            "source_modules": item.get("source_modules") or [],
            "bytes": item["bytes"],
            "sha256": item["sha256"],
            "status": "ok" if ok else "stale",
        })
        if not ok:
            stale.append(item["path"])
    return {
        "status": "ok" if not stale and assets else "stale",
        "detail": "generated demo assets match recorded hashes" if not stale and assets else "demo asset proof is stale",
        "assets": assets,
    }


def _manual_smoke_status():
    if not MANUAL_SMOKE.exists():
        return {
            "status": "missing",
            "detail": "docs/MANUAL_SMOKE_RESULT.md is missing",
        }
    text = MANUAL_SMOKE.read_text(encoding="utf-8")
    if "Result: `hardware-smoke-pass`" in text:
        return {
            "status": "ok",
            "detail": "hardware-smoke-pass recorded",
        }
    if "Result: `not-run`" in text:
        return {
            "status": "blocked",
            "detail": "real keyboard smoke is not run",
        }
    return {
        "status": "blocked",
        "detail": "manual smoke result is not hardware-smoke-pass",
    }


def _proof_matrix_status():
    if not PROOF_MATRIX.exists():
        return {
            "status": "missing",
            "detail": "docs/PROOF_MATRIX.md is missing",
            "claims": 0,
        }
    matrix = _proof_matrix_entries()
    if not matrix:
        return {
            "status": "stale",
            "detail": "docs/PROOF_MATRIX.md has no parseable claim rows",
            "claims": 0,
        }
    return {
        "status": "ok",
        "detail": "docs/PROOF_MATRIX.md maps local-ready, command-gated, and blocked public claims",
        "claims": len(matrix),
    }


def _proof_matrix_entries():
    if not PROOF_MATRIX.exists():
        return []

    entries = []
    section = None
    for raw in PROOF_MATRIX.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line == "## Local Proof":
            section = "local"
            continue
        if line in {
            "## Blocked Until External Proof Exists",
            "## Blocked Until Required Proof Exists",
        }:
            section = "blocked"
            continue
        if line.startswith("## "):
            section = None
            continue
        if not section or not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells[0] in {"Claim", ""}:
            continue
        if len(cells) < 3:
            continue
        claim, verifier, state = cells[:3]
        tier = "blocked" if section == "blocked" else "local"
        if "command-gated" in state.lower() or "release-check.ps1" in verifier:
            tier = "command_gated"
        entries.append({
            "claim": claim,
            "tier": tier,
            "verifier": verifier,
            "status": state,
        })
    return entries


def _proof_summary(entries):
    summary = {"local": 0, "command_gated": 0, "blocked": 0}
    for item in entries:
        if item["tier"] in summary:
            summary[item["tier"]] += 1
    return summary


def build_payload():
    manifest = _manifest_status()
    manual = _manual_smoke_status()
    proof_matrix = _proof_matrix_entries()
    blockers = []
    if manual["status"] != "ok":
        blockers.append(
            "manual keyboard smoke must record hardware-smoke-pass before broad hardware claims")
    return {
        "tool": brand.NAME,
        "version": brand.VERSION,
        "privacy": "No typed text is stored or exported. Key labels and timing-derived verdicts only.",
        "local_proof": {
            "demo_assets": manifest,
            "manual_keyboard_smoke": manual,
            "rich_textual_stack": {
                "status": "ok" if manifest["status"] == "ok" else "blocked",
                "detail": "Rich/Textual demos and bitmap captures are hash-verified; Textual runtime smoke is gated by scripts/verify-textual-app.py" if manifest["status"] == "ok" else "demo provenance is not verified",
            },
            "proof_matrix": _proof_matrix_status(),
        },
        "proof_matrix": proof_matrix,
        "proof_summary": _proof_summary(proof_matrix),
        "public_blockers": blockers,
    }


def print_report(payload):
    ui.proof_report(payload)


def run(args=None):
    args = args or []
    payload = build_payload()
    if "--json" in args:
        print(json.dumps(payload, indent=2))
        return
    print_report(payload)
