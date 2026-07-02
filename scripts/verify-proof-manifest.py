#!/usr/bin/env python3
"""Verify public demo provenance cannot drift from generated assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "site" / "assets" / "keysurgeon-proof.json"
REQUIRED_KINDS = {
    "rich-terminal-demo",
    "rich-terminal-demo-screenshot",
    "textual-command-center-demo",
    "textual-command-center-demo-screenshot",
    "workflow-motion-demo",
    "social-preview",
    "landing-page-desktop-screenshot",
    "landing-page-mobile-screenshot",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    proof = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert proof["schema"] == 1
    assert proof["tool"] == "KeySurgeon"
    assert "no typed private text" in proof["privacy"]

    assets = proof.get("assets") or []
    kinds = {item.get("kind") for item in assets}
    missing = REQUIRED_KINDS - kinds
    assert not missing, missing

    for item in assets:
        path = ROOT / item["path"]
        assert path.exists(), item["path"]
        assert path.stat().st_size == item["bytes"], item["path"]
        assert _sha256(path) == item["sha256"], item["path"]
        assert item.get("generator"), item["path"]
        assert item.get("source_modules"), item["path"]
        assert item.get("evidence"), item["path"]
        for source in item["source_modules"]:
            assert (ROOT / source).exists(), source

    textual = next(item for item in assets if item.get("kind") == "textual-command-center-demo")
    textual_evidence = " ".join(textual.get("evidence") or [])
    assert "verify-textual-app.py" in textual_evidence
    assert "mounts the real Textual app" in textual_evidence
    assert "Windows-style" in textual_evidence

    for name in ("site/assets/keysurgeon-demo.svg", "site/assets/keysurgeon-app.svg"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "<circle" not in text, name
        assert "translate(26,22)" not in text, name

    print("PROOF_MANIFEST_OK", len(assets))


if __name__ == "__main__":
    main()
