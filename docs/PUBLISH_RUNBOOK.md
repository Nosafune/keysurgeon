# Publish Runbook

This is the public v0.2.0 publish sequence. Do not run remote-changing commands
until the repository owner explicitly approves publish in the current session.

## 1. Local Proof

```powershell
.\scripts\local-release-proof.ps1
```

Expected markers:

```text
KEYSURGEON_DEMO_ASSETS_OK
KEYSURGEON_SITE_RENDER_OK
KEYSURGEON_PUBLIC_TREE_OK
KEYSURGEON_RELEASE_ASSET_OK
KEYSURGEON_POST_PUBLISH_GATES_BLOCKED_EXPECTED
KEYSURGEON_LOCAL_RELEASE_PROOF_OK
```

Use `-KeepArtifacts` if you want to inspect `dist\release` after the run:

```powershell
.\scripts\local-release-proof.ps1 -KeepArtifacts
```

## 2. Remote Gate Audit

```powershell
.\scripts\pre-publish-audit.ps1
.\scripts\pre-publish-audit.ps1 -Json
```

Before the repository exists, this should report the uncommitted-release-files
gate, blocked remote gates, and the manual hardware-smoke gate unless
`docs\MANUAL_SMOKE_RESULT.md` records `hardware-smoke-pass`. After commit,
publish, and real-keyboard smoke, it should move toward
`KEYSURGEON_PRE_PUBLISH_READY`. Use `-Json` when a CI job, release packet, or
agent handoff needs structured `status`, `repo`, `checks`, and `failures`
without parsing the human output.

To see the exact release files that would be committed, run the dry-run commit
plan. It prints candidate files and refuses generated artifacts; it does not run
`git add` or `git commit`.

```powershell
.\scripts\release-commit-plan.ps1
```

The commit plan is source-scoped. It also reports distribution-mirror parity
when the adjacent mirror exists, but it does not include that mirror in the
printed source commit command. Publish or copy the mirror only after explicit
approval.

To build a local handoff packet for review or launch preparation without
touching git or GitHub, run:

```powershell
.\scripts\release-packet.ps1
```

The packet writes `artifacts\release-packet\README.md`,
`pre-publish-audit.json`, `release-commit-plan.txt`,
`github-setup-plan.md`, `starter-issues-plan.md`, `proof.json`,
`launch-readiness.md`, `post-publish-audit.json`,
`public-asset-proof.json`, and `launch-copy.md`. It is local evidence only; run
`.\scripts\clean-artifacts.ps1` after inspection.

For a one-page local launch board without building the full packet, run:

```powershell
.\scripts\launch-readiness.ps1
.\scripts\launch-readiness.ps1 -AsMarkdown
```

The launch-readiness script summarizes existing proof and audit data. It does
not commit, push, create issues, create a release, enable Pages, or deploy.

For a read-only remote proof check after the repository, workflows, Pages, and
release are published, run:

```powershell
.\scripts\post-publish-audit.ps1
.\scripts\post-publish-audit.ps1 -Json
```

The post-publish audit verifies repository description, topics, labels, starter
issues, latest selftest and Pages workflow results, GitHub Pages URL, final
`v0.2.0` release status, and the `keysurgeon-v0.2.0-windows-x64.exe` release
asset. It does not mutate GitHub and does not replace the executable smoke
commands below.

If the adjacent distribution mirror is being used as the public handoff tree,
verify that it still matches the source tree before review:

```powershell
.\scripts\verify-dist-parity.ps1
```

The parity check compares source and distribution files while ignoring local
build output, runtime state, caches, logs, and release artifacts.

Record the real-keyboard result with:

```powershell
keysurgeon smoke --check docs\MANUAL_SMOKE_REPORT.md
.\scripts\record-manual-smoke-result.ps1 -Result hardware-smoke-pass -EvidenceReport docs\MANUAL_SMOKE_REPORT.md -Tester "name" -Keyboard "brand model" -InstallSource "local checkout"
```

The CLI check works from a checkout, pip install, or executable artifact. The
CLI check and recorder refuse `hardware-smoke-pass` if the evidence report is
still a blank scaffold or still contains the install-source placeholder.

## 3. Repository Setup

After approval, commit the scoped release files, create or confirm the public
repository, set `origin`, and push the release branch. Then configure:

Generate the exact dry-run command plan first:

```powershell
.\scripts\github-setup-plan.ps1 -Repo nosafune/keysurgeon
.\scripts\github-setup-plan.ps1 -Repo nosafune/keysurgeon -AsMarkdown
```

The setup-plan script prints commands only. It does not call `gh` or change the
remote repository. It includes a guarded `gh repo create` command for the first
publish pass; run it only after explicit approval and only if the repository
does not already exist.

- Description: `Keyboard chatter diagnostic for Windows: catch double-typing, dead keys, and repair-first faults in a Rich/Textual terminal app.`
- Topics: `keyboard`, `keyboard-tester`, `keyboard-diagnostics`, `keyboard-chatter`,
  `keyboard-repair`, `double-typing`, `dead-keys`, `debounce`,
  `mechanical-keyboard`, `usb-hid`, `hardware-diagnostics`, `windows`, `cli`,
  `rich`, `textual`, `repair`.
- Labels: create the labels in `docs/GITHUB_LABELS.md` before enabling public
  intake, including `good first issue` and `help wanted` for seeded starter
  issues.
- Starter issues: use `docs/STARTER_ISSUE_TEMPLATES.md` after labels are
  created so early visitors can contribute board facts, install notes, repair
  wording, tests, or manual smoke evidence.
- Starter issue commands: run `.\scripts\seed-starter-issues-plan.ps1 -AsMarkdown`
  for a local dry-run command packet, then paste/run only after the repository,
  labels, and issue intake exist.
- Issues enabled.
- Social preview: `site/assets/keysurgeon-social.png`.

Do not add a CI badge until the remote self-test workflow has a green run.

## 4. CI And Pages

Wait for `selftest.yml` to pass on the remote branch. The self-test matrix must
cover Python 3.10, 3.11, and 3.12 before the README or release notes claim the
Python 3.10+ install path.

Enable GitHub Pages from Actions, then manually run the `pages` workflow. Do not
claim a homepage URL until the Pages run passes and the URL resolves.

## 5. Optional Executable

For a local release payload proof before remote upload:

```powershell
.\scripts\package-release-asset.ps1
```

This creates `dist\release\keysurgeon-v0.2.0-windows-x64.exe`,
`SHA256SUMS.txt`, `release-manifest.json`, and a copy of the release notes.
The manifest records the executable hash, the public demo proof manifest hash,
and a `proof_snapshot` from `keysurgeon.exe proof --json`. That snapshot must
show demo assets as `ok`, `package_build_gate` as the command-gated package
build, and manual hardware smoke still blocked until real keyboard proof exists.
Attach only the executable after the same smoke has passed on the downloaded
GitHub artifact.

Run the `windows-exe` workflow manually or from a release. Download the
`keysurgeon-windows-release-asset` artifact, keep its `SHA256SUMS.txt`,
`release-manifest.json`, and release notes as proof artifacts, and smoke the
packaged executable:

```powershell
.\keysurgeon.exe --version
.\keysurgeon.exe --plain doctor
.\keysurgeon.exe export --json
.\keysurgeon.exe proof --json
.\keysurgeon.exe selftest
```

Only attach the executable to a release after that smoke passes.

## 6. Release

Use:

- Title: `KeySurgeon v0.2.0 - Forensic Signal`
- Body: `docs/RELEASE_NOTES_0.2.0.md`
- Social/announcement copy: `docs/LAUNCH_PACKET.md`

Run `.\scripts\post-publish-audit.ps1` again after release. Record remaining
blocked gates honestly; do not claim GitHub pop, public visibility, Pages,
starter issue, or release-asset completion until it prints
`KEYSURGEON_POST_PUBLISH_READY`.

## Rollback

- Bad release notes: edit the GitHub release body or delete the draft/release.
- Bad executable asset: delete the asset from the release and rerun the
  executable workflow before replacing it.
- Bad Pages deploy: disable Pages or revert the site commit, then rerun the
  manual `pages` workflow.
- Bad branch push: revert with a normal commit. Do not rewrite published history
  unless the repository owner explicitly approves it.
