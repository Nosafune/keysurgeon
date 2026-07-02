# GitHub Metadata

Recommended public repository settings for KeySurgeon.

Generate a dry-run command plan with:

```powershell
.\scripts\github-setup-plan.ps1 -Repo nosafune/keysurgeon
```

The script prints `gh` commands only and does not change the remote repository.
It includes a guarded `gh repo create` command for the first publish pass and
`gh repo edit` commands for an already-created repository. Run the create
command only after explicit approval and only if the repository does not exist.

After publish, verify the live remote surface with:

```powershell
.\scripts\post-publish-audit.ps1 -Repo nosafune/keysurgeon
```

The audit is read-only. It checks metadata, topics, labels, starter issues,
latest selftest and Pages workflow results, GitHub Pages URL, final `v0.2.0`
release status, and the `keysurgeon-v0.2.0-windows-x64.exe` release asset.

## Description

Keyboard chatter diagnostic for Windows: catch double-typing, dead keys, and
repair-first faults in a Rich/Textual terminal app.

## Topics

```text
keyboard
keyboard-tester
keyboard-diagnostics
keyboard-chatter
keyboard-repair
double-typing
dead-keys
debounce
mechanical-keyboard
usb-hid
hardware-diagnostics
windows
cli
rich
textual
repair
```

## About Links

- Homepage: GitHub Pages after the manual `pages` workflow passes; otherwise
  leave it unset or use the repository README.
- Issues: `https://github.com/nosafune/keysurgeon/issues`
- License: MIT

## Social Preview

Use `site/assets/keysurgeon-social.svg` as the source art. If GitHub requires a
bitmap upload, export it to PNG at 1280x640 and use that file. The same asset
generation pass also captures real desktop and mobile landing-page screenshots
from `site/index.html` with headless Chrome or Edge:

```powershell
.\scripts\generate-demo-assets.ps1
```

Upload `site/assets/keysurgeon-social.png` as the repository social preview.
Use `site/assets/keysurgeon-landing-desktop.png` as the README or release
landing-page screenshot.

The local landing page also carries static Open Graph, Twitter card, and
JSON-LD `SoftwareApplication` metadata that points to the same social preview
asset, local screenshot assets, the planned GitHub repository, issue tracker,
Python runtime, Windows platform, and keyword metadata aligned to the repository
topics. Do not add a canonical public URL, `og:url`, or live homepage claim
until GitHub Pages exists and resolves.

## First Release Notes

Title: `KeySurgeon v0.2.0 - Forensic Signal`

Body source: `docs/RELEASE_NOTES_0.2.0.md`

Summary:

- Rich default terminal UI.
- Optional Textual command center via `keysurgeon app`.
- Local-only runtime storage with `KEYSURGEON_HOME` override.
- GitHub issue templates for bugs, board reports, manual smoke reports, and
  feature requests.
- `docs/STARTER_ISSUE_TEMPLATES.md` starter issue templates for board data,
  install friction, repair wording, test coverage, and manual hardware smoke
  evidence.
- `good first issue` and `help wanted` labels for small public contribution
  lanes after the repository exists.
- `scripts/seed-starter-issues-plan.ps1` dry-run starter issue commands for
  board data, install friction, repair wording, tests, and manual smoke.
- Redacted `keysurgeon export` command for issue attachments.
- Blank issues disabled with contact links to diagnosis, roadmap, and manual
  smoke docs.
- Keyboard tester comparison doc for search visitors who need chatter diagnosis
  instead of a simple key-light page.
- Public landing assets, real headless landing screenshots, workflow demo, and
  actual Rich-rendered diagnosis/app signal-rail demos with browser-rasterized
  PNG captures.
- Static Open Graph, Twitter card, and SoftwareApplication metadata for the
  landing page, including repository, issue tracker, and screenshot fields.
- Package metadata proof that `pyproject.toml` keyword/search positioning
  matches the GitHub topic plan.
- Manual GitHub Pages workflow for publishing the landing page.
- Optional Windows executable artifact workflow.
- Remote selftest workflow runs release-check, site render smoke, install smoke,
  doctor, export, proof, Textual factory import, and wheel-content proof.
- Remote Pages workflow verifies required static files and landing copy before
  deployment.
- Launch copy packet for repository and social surfaces.
- GitHub release-note body with known limits and proof gates.
- Proof matrix for local-ready, command-gated, and externally blocked claims.

Known limits:

- Windows only.
- Requires Python 3.10+ for the current install path.
- Executable workflow exists, but no release asset is published until a GitHub
  release attaches the artifact.
- Pages workflow exists, but no homepage URL exists until the repository is
  created, Pages is enabled from Actions, and the workflow passes.
- Real chattering-key hardware proof should be attached before broad promotion.
