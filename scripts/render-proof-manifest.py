#!/usr/bin/env python3
"""Write public demo provenance for KeySurgeon assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "assets" / "keysurgeon-proof.json"


def _file_proof(path: str) -> dict[str, object]:
    target = ROOT / path
    data = target.read_bytes()
    return {
        "path": path,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> None:
    proof = {
        "schema": 1,
        "tool": "KeySurgeon",
        "purpose": "Public asset provenance for workflow, Rich, Textual, terminal-demo screenshot, landing screenshot, and social proof surfaces.",
        "privacy": "Seeded sample state only; no typed private text is stored or exported.",
        "assets": [
            {
                **_file_proof("site/assets/keysurgeon-demo.svg"),
                "kind": "rich-terminal-demo",
                "generator": "scripts/render-demo-svg.py",
                "source_modules": ["rich_ui.py", "faults.py", "fixes.py", "brand.py"],
                "evidence": [
                    "render-demo-svg.py calls rich_ui.card",
                    "diagnosis evidence is seeded sample output",
                    "repair ladder comes from fixes.ladder_for",
                    "export_svg uses KeySurgeon's Windows-style demo frame, not Rich's default macOS-style terminal chrome",
                ],
            },
            {
                **_file_proof("site/assets/keysurgeon-demo.png"),
                "kind": "rich-terminal-demo-screenshot",
                "generator": "scripts/export-terminal-screenshots.ps1",
                "source_modules": ["site/assets/keysurgeon-demo.svg", "scripts/render-demo-svg.py"],
                "evidence": [
                    "export-terminal-screenshots.ps1 rasterizes the current Rich demo SVG through a headless browser",
                    "the PNG is a public bitmap capture of the verified Rich demo surface with Windows-style framing, not a live interactive terminal screenshot",
                ],
            },
            {
                **_file_proof("site/assets/keysurgeon-app.svg"),
                "kind": "textual-command-center-demo",
                "generator": "scripts/render-app-svg.py",
                "source_modules": ["app_textual.py", "faults.py", "brand.py"],
                "evidence": [
                    "render-app-svg.py calls app_textual hero, signal rail, command center, device, readiness, repair ladder, action bar, issue packet, CLI flow, and health map builders",
                    "watcher state is seeded sample output",
                    "selftest verifies app text avoids fake metrics and fake readiness",
                    "verify-textual-app.py mounts the real Textual app headlessly and presses proof, issue, and watch bindings",
                    "export_svg uses KeySurgeon's Windows-style demo frame, not Rich's default macOS-style terminal chrome",
                ],
            },
            {
                **_file_proof("site/assets/keysurgeon-app.png"),
                "kind": "textual-command-center-demo-screenshot",
                "generator": "scripts/export-terminal-screenshots.ps1",
                "source_modules": ["site/assets/keysurgeon-app.svg", "scripts/render-app-svg.py", "app_textual.py"],
                "evidence": [
                    "export-terminal-screenshots.ps1 rasterizes the current Textual command-center demo SVG through a headless browser",
                    "verify-textual-app.py separately mounts the real Textual app headlessly and checks core actions",
                    "the PNG is a public bitmap capture of the verified app demo surface with Windows-style framing, not a live interactive terminal screenshot",
                ],
            },
            {
                **_file_proof("site/assets/keysurgeon-flow.svg"),
                "kind": "workflow-motion-demo",
                "generator": "scripts/render-flow-svg.py",
                "source_modules": ["scripts/render-flow-svg.py"],
                "evidence": [
                    "render-flow-svg.py writes the README workflow demo from command/evidence frames",
                    "the demo shows watch, test, fix, and proof commands",
                    "seeded copy avoids private typed text and remote claims",
                ],
            },
            {
                **_file_proof("site/assets/keysurgeon-social.png"),
                "kind": "social-preview",
                "generator": "scripts/export-social-preview.ps1",
                "source_modules": ["site/assets/keysurgeon-social.svg"],
                "evidence": [
                    "export-social-preview.ps1 renders the SVG through a headless browser",
                    "PNG is intended for GitHub social preview upload",
                ],
            },
            {
                **_file_proof("site/assets/keysurgeon-landing-desktop.png"),
                "kind": "landing-page-desktop-screenshot",
                "generator": "scripts/export-landing-screenshots.ps1",
                "source_modules": ["site/index.html", "site/assets/keysurgeon.css"],
                "evidence": [
                    "export-landing-screenshots.ps1 renders the local landing page through a headless browser",
                    "desktop capture uses the public site HTML and CSS, not a mockup",
                ],
            },
            {
                **_file_proof("site/assets/keysurgeon-landing-mobile.png"),
                "kind": "landing-page-mobile-screenshot",
                "generator": "scripts/export-landing-screenshots.ps1",
                "source_modules": ["site/index.html", "site/assets/keysurgeon.css"],
                "evidence": [
                    "export-landing-screenshots.ps1 renders the local landing page through a headless browser",
                    "mobile capture uses the public site HTML and CSS, not a mockup",
                ],
            },
        ],
    }

    OUT.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(f"KEYSURGEON_PROOF_MANIFEST_OK {OUT} {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
