# KeySurgeon v0.2.1

Bugfix and cleanup release.

## Fixed

- A crash in the readiness panel renderer. `"bold ks.signal"` is not a valid
  Rich style string, so the affected panel raised `rich.errors.MissingStyle`
  whenever it rendered. The style now uses the brand color directly.

## Removed

- The `keysurgeon ready` command. It summarized internal release-process
  state, not keyboard diagnostics. `keysurgeon proof` (and `proof --json`)
  remains and now reports local diagnostic proof only: demo asset provenance,
  privacy posture, the claim matrix, and manual hardware-smoke status.
- Internal release-process scripts and docs from the public tree.

## Changed

- CI's public-tree verifier is now a small behavior check that actually fails
  on a selftest failure, instead of asserting exact doc phrasing.
- README and public docs trimmed and rewritten.

No diagnostic logic changed in this release. Fault classification, scoring,
watch mode, exports, and the repair ladder are identical to 0.2.0.
