# Support

Use GitHub issues for public support:

- **Bug report** for crashes, install failures, or wrong diagnoses.
- **Board report** when KeySurgeon guesses your keyboard type incorrectly or
  needs model metadata.
- **Feature or diagnostic request** for scoped product improvements.
- **Manual smoke report** when validating real keyboard behavior before a
  release claim. Use the manual smoke issue form after completing
  `docs/MANUAL_SMOKE_REPORT.md`.

Blank issues are disabled so reports keep the evidence KeySurgeon needs.

Before filing, run:

```powershell
keysurgeon selftest
keysurgeon --version
keysurgeon --plain doctor
keysurgeon proof --json
keysurgeon issue --out KEYSURGEON_ISSUE_PACKET.md
```

For bug reports, prefer `keysurgeon issue`; it combines a path-redacted support
summary, proof, and redacted export sections into one Markdown packet. Use
`keysurgeon export --json` too when a saved test, sweep, or watch session needs
separate structured output.

Do not paste typed private text. Key labels, timing metrics, verdicts, model
names, asset proof, readiness blockers, and stack traces are enough.
