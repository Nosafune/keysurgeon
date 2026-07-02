# Roadmap

KeySurgeon should stay narrow enough to be trusted. New checks only belong in
the product when they can produce evidence without storing typed private text or
pretending to measure hardware behavior the tool cannot actually see.

## Proven In v0.2.0

- Chatter, dead-key, intermittent, sticky, and extra-event classification.
- Rich terminal cards with plain and no-color fallbacks.
- Optional Textual command center backed by saved report and watcher state.
- Textual watch toggle, device panel, and next-command guidance without fake
  diagnostic actions.
- Background watch mode for double-fire evidence while typing normally.
- Board-type memory and conservative keyboard model hints.
- Redacted Markdown/JSON exports for GitHub issues and repair notes.
- Local-only runtime JSON with `KEYSURGEON_HOME` override.
- `selftest`, `doctor`, public-tree verifier, package build, and optional
  Windows executable workflow.

## Candidate Next Lanes

| Lane | Why it matters | Proof needed before release |
|---|---|---|
| More board model data | Better repair ladders for known hot-swap/soldered models. | Issue reports or vendor/manual evidence for each model. |
| Installer/release asset | Lowers friction for non-Python users. | Built artifact attached to a release and smoke-tested. |
| GitHub Pages homepage | Better first impression than a repository-only visit. | Manual Pages workflow passes and URL resolves. |

## Cut Until Proven

- Latency benchmarking.
- NKRO or rollover certification.
- Scancode/remapping claims.
- Live repair actions.
- Telemetry, cloud sync, or private text capture.

These may become future features only if the implementation can prove them with
honest local evidence. Until then, the CLI may route users back to direct key
testing or issue collection rather than pretending the check exists.

## Contribution Fit

Good issues include reproducible key behavior, non-private KeySurgeon output,
keyboard model details, or specific repair-ladder corrections. Broad requests
for remapping, macro layers, game performance tuning, or general keyboard
shopping are outside the current product.
