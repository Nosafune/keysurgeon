# Proof Matrix

This matrix keeps public claims tied to local evidence. It is for README,
release, and GitHub visitors who need to know what is proven now and what still
requires hardware or remote proof.

## Local Proof

| Claim | Proof command or file | Current status |
|---|---|---|
| Rich terminal output is wired | `python keysurgeon.py selftest`, `site/assets/keysurgeon-demo.svg`, and `site/assets/keysurgeon-demo.png` | Proven locally; PNG is a browser-rasterized capture of the verified Rich demo renderer with Windows-style terminal framing. |
| Textual command center is wired | `python keysurgeon.py selftest`, `python scripts/verify-textual-app.py`, `site/assets/keysurgeon-app.svg`, and `site/assets/keysurgeon-app.png` | Proven locally by factory/selftest coverage, generated app demo, PNG capture, and headless Textual mount/action smoke. |
| Landing page has real local screenshots | `.\scripts\generate-demo-assets.ps1` | Proven locally by headless desktop and mobile PNGs. |
| Public assets are current | `.\scripts\verify-public-tree.ps1` | Proven locally by asset hashes and sentinel checks. |
| Package metadata matches search positioning | `keysurgeon proof --json`, `pyproject.toml`, and `.\scripts\verify-public-tree.ps1` | Proven locally; package keywords include the repair/search terms used by the GitHub topic plan. |
| Package build path works | `.\scripts\release-check.ps1` | Command-gated local proof. |
| Local release package can be built | `.\scripts\local-release-proof.ps1` | Local-only proof; release artifacts are cleaned after verification unless kept intentionally. |
| Export avoids typed private text | `python keysurgeon.py selftest` and `python keysurgeon.py export --json` | Proven locally by redacted export checks. |
| Chatter timing logic works | `python keysurgeon.py selftest` | Proven locally with synthetic hook replay. |

## Blocked Until Required Proof Exists

| Claim | Required proof | Why blocked |
|---|---|---|
| Release files are committed | `git status --porcelain -- .` is clean before publish | Local v2 files must be committed before any public push or tag. |
| Broad real-keyboard hardware behavior | `docs/MANUAL_SMOKE_RESULT.md` records `hardware-smoke-pass` after `docs/MANUAL_KEYBOARD_SMOKE.md` | Requires an interactive real Windows keyboard run. |
| Public GitHub repository exists | `git remote get-url origin`, `gh repo view nosafune/keysurgeon`, and `.\scripts\post-publish-audit.ps1 -Json` | No repository or origin remote is configured yet. |
| Remote selftest is green | Latest `selftest.yml` GitHub Actions run succeeds and `.\scripts\post-publish-audit.ps1 -Json` reports it. | Requires pushed GitHub workflow run. |
| GitHub Pages homepage exists | Latest `pages.yml` GitHub Actions run succeeds, URL resolves, and `.\scripts\post-publish-audit.ps1 -Json` reports a Pages URL. | Requires repository, Pages setup, and remote workflow pass. |
| GitHub release asset exists | Final non-draft/non-prerelease `v0.2.0` GitHub release contains a smoke-tested `keysurgeon-v0.2.0-windows-x64.exe` asset and `.\scripts\post-publish-audit.ps1 -Json` reports it. | Requires repository release and downloaded artifact smoke. |
| GitHub visibility is complete | `.\scripts\post-publish-audit.ps1` prints `KEYSURGEON_POST_PUBLISH_READY` | Requires repository metadata, labels, starter issues, selftest, Pages, final release status, and release asset proof. |

## Reporting Rule

Use local proof language until the matching external proof exists:

- Say `local-ready` for source, assets, and package checks that pass locally.
- Say `command-gated` for proofs that are produced and cleaned by release
  scripts.
- Say `blocked` for uncommitted release files, hardware, GitHub, Pages, workflow,
  and release claims that need external evidence.
- Say `published-visible` only after `.\scripts\post-publish-audit.ps1` prints
  `KEYSURGEON_POST_PUBLISH_READY`.
