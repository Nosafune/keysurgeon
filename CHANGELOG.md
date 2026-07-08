# Changelog

## 0.2.1 - 2026-07-08

- Fix a crash in the launch-readiness renderer: `"bold ks.signal"` is not a
  valid Rich style, so any command that rendered that panel raised
  `MissingStyle`.
- Remove the `keysurgeon ready` command and the release-process machinery
  (`launch-readiness`, `pre/post-publish audits`, `release packet/commit plan`,
  GitHub setup planning) from the CLI, Textual app, and scripts. `keysurgeon
  proof` now reports local diagnostic proof only: demo asset provenance,
  privacy, the claim matrix, and hardware-smoke status.
- Rewrite `scripts/verify-public-tree.ps1` as a small behavior check (selftest,
  no internal agent files, public assets present, proof manifest) that fails CI
  on a real failure instead of asserting doc phrasing.
- Trim README and public docs; remove internal release-process docs from the
  public tree.

## 0.2.0 - 2026-06-30

- Add Forensic Signal brand tokens.
- Add Rich-backed default terminal renderer with `--plain` / `--no-color` fallback.
- Add optional `keysurgeon app` Textual command center.
- Update package metadata for Rich and Textual.
- Add landing assets, product contract, GitHub issue templates, and release docs.
- Generate the public demo SVG from the actual Rich renderer.
- Rename the profile persistence module to avoid Python stdlib `profile` collisions after install.
- Extend CI/release checks to verify installed Rich/Textual imports.
- Add optional PyInstaller Windows executable build script and artifact workflow.
- Add `keysurgeon doctor` support/environment check.
- Add redacted `keysurgeon export` reports for GitHub issues and repair notes.
- Add one-command local release proof, release-asset packaging, and manual-smoke gate.
- Add repeatable social-preview PNG export script.
- Add full public-tree verifier for release files, assets, scrub, and runtime checks.
- Add synthetic hook replay tests for `trials.chatter_trial` timing stats.
- Add public roadmap for supported checks, candidate next lanes, and non-claims.
- Add starter-issue and proof-matrix docs for public intake and release-truth
  review.
- Add a no-mutation `launch-readiness.ps1` board that summarizes existing
  proof and pre-publish audit data for release review.
- Add a read-only `post-publish-audit.ps1` gate for GitHub metadata, labels,
  starter issues, remote workflows, Pages URL, and release asset visibility.
- Harden the manual smoke result recorder so `hardware-smoke-pass` rejects blank
  evidence scaffolds, missing keyboard identity, placeholder install sources,
  and unfilled result tables.
- Add `keysurgeon smoke --check` so checkout, pip, and executable users can
  validate a filled smoke report before recording `hardware-smoke-pass`.

## 0.1.0 - 2026-06-30

- Prepare public distribution metadata.
- Add `--help` and `--version`.
- Move runtime JSON to a per-user data directory with `KEYSURGEON_HOME` override.
- Keep self-test available from the package entrypoint.
