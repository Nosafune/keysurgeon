# Release Checklist

Use this before tagging or pushing a public KeySurgeon release.

## Local Checks

Full public-tree verification:

```powershell
.\scripts\verify-public-tree.ps1
```

Complete local release proof:

```powershell
.\scripts\local-release-proof.ps1
```

Runtime/package verification only:

```powershell
.\scripts\release-check.ps1
```

Read-only publish gate audit:

```powershell
.\scripts\pre-publish-audit.ps1
.\scripts\pre-publish-audit.ps1 -Json
```

Read-only post-publish visibility audit:

```powershell
.\scripts\post-publish-audit.ps1
.\scripts\post-publish-audit.ps1 -Json
```

Local release review packet:

```powershell
.\scripts\release-packet.ps1
```

One-page local launch board:

```powershell
keysurgeon ready
.\scripts\launch-readiness.ps1
.\scripts\launch-readiness.ps1 -AsMarkdown
```

Public release copy check, if you maintain a separate public release copy:

```powershell
.\scripts\verify-dist-parity.ps1
```

Publish sequence:

```powershell
Get-Content .\docs\PUBLISH_RUNBOOK.md
```

Regenerate public demo/social assets:

```powershell
.\scripts\generate-demo-assets.ps1
```

This must refresh `site/assets/keysurgeon-demo.svg`,
`site/assets/keysurgeon-demo.png`, `site/assets/keysurgeon-app.svg`,
`site/assets/keysurgeon-app.png`, `site/assets/keysurgeon-flow.svg`, and
`site/assets/keysurgeon-proof.json`.

Render-check the landing page:

```powershell
.\scripts\verify-site-render.ps1
```

Expected proof:

- `local-release-proof.ps1` prints `KEYSURGEON_LOCAL_RELEASE_PROOF_OK`.
- Python files compile.
- `keysurgeon.py selftest` passes.
- Selftest includes synthetic hook replay coverage for chatter timing stats.
- `keysurgeon.py --version` prints the release version.
- `keysurgeon.py --plain doctor` prints support facts.
- `keysurgeon.py ready` reports the local launch board with no remote mutation.
- `keysurgeon.py proof --json` reports hash-verified demo assets and honest blockers.
- Textual app factory imports.
- `python .\scripts\verify-textual-app.py` prints `KEYSURGEON_TEXTUAL_APP_SMOKE_OK`.
- A wheel builds under `dist/`.
- Landing page renders to desktop and mobile screenshots.
- Release asset package builds and smokes locally.
- `local-release-proof.ps1` runs the post-publish audit and prints
  `KEYSURGEON_POST_PUBLISH_GATES_BLOCKED_EXPECTED` while live GitHub visibility
  proof is absent.

## Optional Windows Executable

```powershell
.\scripts\build-exe.ps1
.\dist\keysurgeon.exe --version
.\dist\keysurgeon.exe --plain doctor
.\dist\keysurgeon.exe export --json
.\dist\keysurgeon.exe proof --json
.\dist\keysurgeon.exe selftest
```

The `.github/workflows/windows-exe.yml` workflow builds the same release asset
package as a GitHub artifact on manual dispatch or release creation. This is
not the same as publishing an installer; do not claim an `.exe` release until
the `keysurgeon-windows-release-asset` artifact is downloaded, smoke-tested,
and attached to a GitHub release.

Local release-asset package:

```powershell
.\scripts\package-release-asset.ps1
Get-Content .\dist\release\SHA256SUMS.txt
Get-Content .\dist\release\release-manifest.json
```

Expected marker:

```text
KEYSURGEON_RELEASE_ASSET_OK
KEYSURGEON_RELEASE_PROOF_SHA256
```

The release manifest must include `public_demo_proof` for
`site/assets/keysurgeon-proof.json` and a `proof_snapshot` showing demo assets
are `ok`, `package_build_gate` records the command-gated package build, and
manual keyboard smoke remains blocked until real hardware proof is recorded.

Clean generated artifacts after inspection:

```powershell
.\scripts\clean-artifacts.ps1
```

## Manual Keyboard Smoke

Run the manual smoke in `docs/MANUAL_KEYBOARD_SMOKE.md` on a real Windows
keyboard before claiming hardware behavior is proven. Record the result with
`docs/MANUAL_SMOKE_REPORT.md`.

```powershell
.\scripts\manual-keyboard-smoke.ps1
```

This creates `.runtime\manual-smoke\MANUAL_SMOKE_REPORT.md` with safe
non-interactive checks plus the required interactive commands. It is not a pass
until those interactive commands are run on real hardware.

After the real-keyboard pass, update `docs\MANUAL_SMOKE_RESULT.md` to
`hardware-smoke-pass`. `scripts\pre-publish-audit.ps1` blocks until that result
is recorded.

First validate the filled report from the checkout, pip install, or executable
artifact:

```powershell
keysurgeon smoke --check docs\MANUAL_SMOKE_REPORT.md
```

Prefer the recorder command so the gate file stays parseable:

```powershell
.\scripts\record-manual-smoke-result.ps1 -Result hardware-smoke-pass -EvidenceReport docs\MANUAL_SMOKE_REPORT.md -Tester "name" -Keyboard "brand model" -InstallSource "local checkout"
```

The CLI check and recorder both reject blank scaffolds for
`hardware-smoke-pass`; the evidence report must include keyboard identity, a
real install source, filled result table cells, and an explicit
`hardware-smoke-pass` release claim.

## GitHub Release Surface

Before publishing:

- Run `.\scripts\pre-publish-audit.ps1`. It must either print
  `KEYSURGEON_PRE_PUBLISH_READY` or list the exact remote/local gates still
  blocking publish. Use `.\scripts\pre-publish-audit.ps1 -Json` for structured
  release-packet or CI evidence.
- Confirm the v2 release files are committed; `pre-publish-audit.ps1` blocks on
  `release files committed` while local tracked or untracked release files
  remain under KeySurgeon.
- Run `.\scripts\release-commit-plan.ps1` before any commit. It is dry-run only,
  prints the scoped candidate files, fails if generated artifacts are present,
  and reports whether the separate public release copy is in sync. The source
  commit command does not include that copy; publish or copy it only
  after explicit approval.
- Run `.\scripts\release-packet.ps1` when a reviewer or launch
  prep pass needs one local folder containing audit JSON, the dry-run commit
  plan, the GitHub setup plan, proof JSON, the launch-readiness board,
  post-publish audit JSON, asset proof, and launch copy.
- Confirm `selftest.yml` covers Python 3.10, 3.11, and 3.12 before adding any
  badge or release claim that says Python 3.10+.
- Run `.\scripts\github-setup-plan.ps1 -Repo nosafune/keysurgeon` and review
  the dry-run repository commands before applying GitHub settings manually.
- Follow `docs/PUBLISH_RUNBOOK.md` for the approved publish sequence and
  rollback path.
- Create or confirm the public repository exists.
- Add the self-test badge only after the workflow exists remotely and has a
  green run. The workflow must prove release-check, landing render, installed
  command smoke, doctor, export, and Textual import.
- Set repository description to: `Keyboard chatter diagnostic for Windows: catch double-typing, dead keys, and repair-first faults in a Rich/Textual terminal app.`
- Add topics: `keyboard`, `keyboard-tester`, `keyboard-diagnostics`, `keyboard-chatter`,
  `keyboard-repair`, `double-typing`, `dead-keys`, `debounce`,
  `mechanical-keyboard`, `usb-hid`, `hardware-diagnostics`, `windows`, `cli`,
  `rich`, `textual`, `repair`.
- Create the labels in `docs/GITHUB_LABELS.md` before enabling public issue
  intake, including `good first issue` and `help wanted` for seeded starter
  issues.
- Seed starter issues from `docs/STARTER_ISSUE_TEMPLATES.md` after labels
  exist and before broad announcement posts.
- Generate the dry-run starter issue command plan with
  `.\scripts\seed-starter-issues-plan.ps1 -AsMarkdown` before creating issues.
- Set the social preview to `site/assets/keysurgeon-social.svg` or an exported PNG derived from it.
- If GitHub requires PNG, run `.\scripts\generate-demo-assets.ps1` and upload
  `site/assets/keysurgeon-social.png`.
- Confirm issues are enabled so the bug and board report templates appear.
- Enable GitHub Pages from Actions, then run the manual `pages` workflow after
  the repository exists. Do not claim a homepage URL until that workflow passes.
- Confirm the release notes match `CHANGELOG.md`.
- Use `docs/RELEASE_NOTES_0.2.0.md` as the GitHub release body for v0.2.0.
- Use `docs/LAUNCH_PACKET.md` for public copy after replacing only URLs that
  resolve.
- If shipping an executable, attach the packaged
  `dist/release/keysurgeon-v0.2.0-windows-x64.exe` from the
  `keysurgeon-windows-release-asset` workflow artifact and run the executable
  smoke first. Keep `SHA256SUMS.txt`, `release-manifest.json`, and release notes
  as release proof artifacts.
- After repository metadata, labels, starter issues, selftest, Pages, and the
  release asset exist, run `.\scripts\post-publish-audit.ps1`. It must print
  `KEYSURGEON_POST_PUBLISH_READY` before launch copy claims public visibility is
  complete.

## Publish Status Labels

Report status honestly:

- `local only`: files exist locally, not committed or pushed.
- `committed`: committed locally, not pushed.
- `pushed`: remote GitHub branch has the release files.
- `pages-published`: GitHub Pages URL exists and the manual `pages` workflow passed.
- `published`: GitHub release/tag exists.
