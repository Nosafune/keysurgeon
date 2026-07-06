# KeySurgeon v0.2.0 - Forensic Signal

KeySurgeon v0.2.0 turns the project into a public-ready Windows terminal
diagnostic for keyboard chatter and fixable key faults.

## Highlights

- Rich default terminal UI with readable diagnostic cards.
- Optional Textual command center through `keysurgeon app`, including real
  watch start/stop, device identity, and next-command guidance.
- Headless Textual runtime smoke for the app mount and core proof/issue/watch
  bindings.
- Plain and no-color output for logs, automation, and simple terminals.
- Local-only runtime storage with `KEYSURGEON_HOME` override.
- `keysurgeon doctor` for support/environment checks.
- Synthetic hook replay tests for timing stats without requiring a physical
  keyboard.
- Public landing page, brand assets, social preview, reproducible headless landing screenshots, and browser-rasterized Rich/Textual demo PNGs plus workflow and source SVG generation.
- Static Open Graph, Twitter card, and SoftwareApplication metadata for the
  landing page, wired to the generated social preview, repository, issue
  tracker, and screenshot fields.
- GitHub issue templates for bugs, board reports, manual smoke reports, and
  feature requests.
- Starter-issue and proof-matrix docs that separate local proof from hardware
  and GitHub publish blockers.
- No-mutation launch-readiness board that summarizes proof and pre-publish audit
  data without touching git, GitHub, releases, Pages, or deploy state.
- Read-only post-publish audit for repository metadata, labels, starter issues,
  remote workflow runs, Pages URL, and release asset visibility.
- Hardened manual smoke pass recorder that refuses `hardware-smoke-pass` when
  evidence is still a blank scaffold or missing keyboard/run details.
- Installed/executable-friendly `keysurgeon smoke --check` validation before
  recording `hardware-smoke-pass`.
- Package metadata proof for search/topic keyword parity.
- Redacted `keysurgeon export` output for GitHub issues and repair notes.
- Manual GitHub Pages workflow and optional Windows executable artifact workflow.

## What It Diagnoses

- Chatter: one press registers twice.
- Dead keys: a requested key does not respond.
- Intermittent keys: a key registers sometimes and misses sometimes.
- Sticky behavior: hold or release timing looks wrong.
- Extra events: late bounces after the expected press/release pattern.

## Verification Before Release

Run:

```powershell
.\scripts\verify-public-tree.ps1
.\scripts\pre-publish-audit.ps1
.\scripts\post-publish-audit.ps1
```

The public-tree verifier must pass before tagging. The pre-publish audit may
still report blocked remote gates until the public repository, workflow runs,
Pages deployment, and release asset exist.
The post-publish audit is expected to stay blocked until the live GitHub
repository, labels, starter issues, workflows, Pages URL, and release asset are
visible.

## Known Limits

- Windows only.
- Requires Python 3.10+ for the current install path.
- No PyPI, Winget, installer, or published GitHub release asset exists until it
  is explicitly created and verified.
- The optional executable workflow is not a release by itself; attach and smoke
  test the built artifact before advertising an `.exe`.
- Do not claim broad real-hardware proof until the manual keyboard smoke has run
  on a physical keyboard.
- Latency benchmarking, NKRO certification, scancode/remapping claims, telemetry,
  and live repair actions are not part of v0.2.0.

## Suggested GitHub Release Body

```text
KeySurgeon v0.2.0 is the first public-ready Forensic Signal release: a Windows
terminal diagnostic for keyboard chatter and fixable key faults.

Highlights:
- Rich diagnostic cards by default.
- Optional Textual command center with real saved report/watcher state.
- Markdown/JSON diagnostic export that avoids typed private text.
- Plain/no-color output for logs and automation.
- Local-only runtime data; no telemetry and no typed text storage.
- `selftest`, `doctor`, public-tree verifier, and reproducible workflow/Rich/app
  launch assets, plus a headless Textual app smoke.
- Launch-readiness board and hardened manual-smoke gate for honest pre-publish
  review.

Known limits:
- Windows only.
- Python install path first; no installer/PyPI/Winget yet.
- Real keyboard smoke must be attached before broad hardware claims.
```
