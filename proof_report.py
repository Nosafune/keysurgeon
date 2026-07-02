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
RELEASE_MANIFEST = ROOT / "dist" / "release" / "release-manifest.json"
RELEASE_CHECK = ROOT / "scripts" / "release-check.ps1"
PYPROJECT = ROOT / "pyproject.toml"


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


def _package_build_gate_status():
    missing = []
    if not RELEASE_CHECK.exists():
        missing.append("scripts/release-check.ps1")
    if not PYPROJECT.exists():
        missing.append("pyproject.toml")
    if missing:
        return {
            "status": "missing",
            "detail": "package build gate is missing: " + ", ".join(missing),
            "command": "scripts/release-check.ps1",
        }
    return {
        "status": "command-gated",
        "detail": "wheel/package build proof is produced by scripts/release-check.ps1 and is intentionally cleaned after verification",
        "command": "scripts/release-check.ps1",
    }


def _load_pyproject_metadata():
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
        tomllib = None

    text = PYPROJECT.read_text(encoding="utf-8")
    if tomllib:
        data = tomllib.loads(text)
        project = data.get("project") or {}
        return {
            "keywords": list(project.get("keywords") or []),
            "urls": dict(project.get("urls") or {}),
        }

    keyword_match = re.search(r"(?ms)^keywords\s*=\s*\[(.*?)^\]", text)
    keywords = []
    if keyword_match:
        keywords = re.findall(r'"([^"]+)"', keyword_match.group(1))

    urls = {}
    url_match = re.search(r"(?ms)^\[project\.urls\]\s*(.*?)(?:^\[|\Z)", text)
    if url_match:
        for key, value in re.findall(r'(?m)^([A-Za-z0-9_-]+)\s*=\s*"([^"]+)"', url_match.group(1)):
            urls[key] = value
    return {"keywords": keywords, "urls": urls}


def _package_metadata_status():
    if not PYPROJECT.exists():
        return {
            "status": "missing",
            "detail": "pyproject.toml is missing",
            "keywords": [],
            "urls": {},
        }

    try:
        metadata = _load_pyproject_metadata()
    except Exception as exc:
        return {
            "status": "stale",
            "detail": f"pyproject.toml metadata could not be read: {exc}",
            "keywords": [],
            "urls": {},
        }

    keywords = metadata["keywords"]
    keyword_set = set(keywords)
    required = {
        "keyboard-tester",
        "keyboard-diagnostics",
        "keyboard-chatter",
        "keyboard-repair",
        "double-typing",
        "dead-keys",
        "debounce",
        "mechanical-keyboard",
        "usb-hid",
        "hardware-diagnostics",
        "rich",
        "textual",
        "repair",
    }
    missing = sorted(required - keyword_set)
    urls = metadata["urls"]
    expected_urls = {"Homepage", "Repository", "Issues", "Changelog"}
    missing_urls = sorted(expected_urls - set(urls))
    problems = []
    if missing:
        problems.append("missing keywords: " + ", ".join(missing))
    if missing_urls:
        problems.append("missing project URLs: " + ", ".join(missing_urls))

    return {
        "status": "ok" if not problems else "stale",
        "detail": (
            f"pyproject search metadata includes {len(keywords)} keywords and planned GitHub URLs"
            if not problems else "; ".join(problems)
        ),
        "keywords": keywords,
        "urls": urls,
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


def _next_actions():
    return [
        {
            "label": "Build local release packet",
            "command": ".\\scripts\\release-packet.ps1",
            "proof": "writes local audit, commit plan, setup plan, proof JSON, post-publish audit JSON, asset proof, and launch copy under artifacts/release-packet",
            "changes_remote": False,
        },
        {
            "label": "Review scoped commit plan",
            "command": ".\\scripts\\release-commit-plan.ps1",
            "proof": "prints the release candidate file list and refuses generated artifacts",
            "changes_remote": False,
        },
        {
            "label": "Record real keyboard smoke",
            "command": "keysurgeon smoke --check docs\\MANUAL_SMOKE_REPORT.md",
            "proof": "validates the filled report before scripts/record-manual-smoke-result.ps1 records hardware-smoke-pass",
            "changes_remote": False,
        },
        {
            "label": "Prepare GitHub setup commands",
            "command": ".\\scripts\\github-setup-plan.ps1 -Repo nosafune/keysurgeon -AsMarkdown",
            "proof": "prints dry-run repository description, topics, labels, and social-preview steps",
            "changes_remote": False,
        },
        {
            "label": "Verify live post-publish surface",
            "command": ".\\scripts\\post-publish-audit.ps1 -Json",
            "proof": "checks metadata, labels, starter issues, selftest, Pages, final v0.2.0 release status, and release asset visibility without mutating GitHub",
            "changes_remote": False,
        },
    ]


def _release_package_status():
    if not RELEASE_MANIFEST.exists():
        return {
            "status": "blocked",
            "detail": "local release package proof is not built",
            "manifest": "dist/release/release-manifest.json",
        }

    try:
        release = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return {
            "status": "stale",
            "detail": f"release manifest is invalid JSON: {exc.msg}",
            "manifest": "dist/release/release-manifest.json",
        }

    problems = []
    asset = release.get("asset") or {}
    asset_file = asset.get("file")
    if not asset_file:
        problems.append("asset file is missing from release manifest")
    else:
        asset_path = RELEASE_MANIFEST.parent / asset_file
        if not asset_path.exists():
            problems.append(f"{asset_file} is missing")
        else:
            if asset_path.stat().st_size != asset.get("bytes"):
                problems.append(f"{asset_file} byte count is stale")
            if _sha256(asset_path) != asset.get("sha256"):
                problems.append(f"{asset_file} sha256 is stale")

    public_proof = release.get("public_demo_proof") or {}
    if not MANIFEST.exists():
        problems.append("current public proof manifest is missing")
    else:
        if public_proof.get("sha256") != _sha256(MANIFEST):
            problems.append("public demo proof hash is stale")
        if public_proof.get("bytes") != MANIFEST.stat().st_size:
            problems.append("public demo proof byte count is stale")

    snapshot = release.get("proof_snapshot") or {}
    if snapshot.get("demo_assets") != "ok":
        problems.append("proof snapshot does not verify demo assets")
    if snapshot.get("manual_keyboard_smoke") == "ok":
        problems.append("proof snapshot unexpectedly claims hardware smoke pass")

    return {
        "status": "ok" if not problems else "stale",
        "detail": (
            "local release package matches executable and demo proof hashes"
            if not problems else "; ".join(problems)
        ),
        "manifest": "dist/release/release-manifest.json",
        "asset": asset_file,
        "public_demo_proof": public_proof.get("sha256"),
    }


def build_payload():
    manifest = _manifest_status()
    manual = _manual_smoke_status()
    package_build_gate = _package_build_gate_status()
    proof_matrix = _proof_matrix_entries()
    release_package = _release_package_status()
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
            "package_metadata": _package_metadata_status(),
            "package_build_gate": package_build_gate,
            "proof_matrix": _proof_matrix_status(),
            "release_package": release_package,
        },
        "proof_matrix": proof_matrix,
        "proof_summary": _proof_summary(proof_matrix),
        "public_blockers": [
            "manual keyboard smoke must record hardware-smoke-pass before broad hardware claims",
            "GitHub repository, remote selftest workflow, Pages workflow, final v0.2.0 release, and release proof must exist before publish claims",
            "post-publish-audit.ps1 must report KEYSURGEON_POST_PUBLISH_READY before claiming GitHub visibility is complete",
            "release files must be committed before any public push or tag",
        ],
        "next_actions": _next_actions(),
    }


def print_report(payload):
    ui.proof_report(payload)


def print_ready(payload):
    ui.ready_report(payload)


def run(args=None):
    args = args or []
    payload = build_payload()
    if "--json" in args:
        print(json.dumps(payload, indent=2))
        return
    print_report(payload)
