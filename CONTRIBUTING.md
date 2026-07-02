# Contributing

KeySurgeon is useful only if its diagnostics stay honest. Contributions should
improve real keyboard diagnosis, repair guidance, packaging, or documentation
without inventing unsupported capabilities.

## Good First Contributions

- Add or correct keyboard model metadata in `boards.py`.
- Improve repair-ladder wording for a proven board/fault combination.
- Add self-test coverage for faults, scoring, storage, or board detection.
- Improve Windows install notes or troubleshooting docs.

Use `docs/FIRST_ISSUES.md` for starter issue scope and
`docs/STARTER_ISSUE_TEMPLATES.md` for ready-to-post issue bodies before opening
public intake.

## Before Opening A Pull Request

Use `.github/PULL_REQUEST_TEMPLATE.md` and keep the evidence section current.

```powershell
$files = Get-ChildItem -Filter *.py -File | ForEach-Object { $_.FullName }
python -m py_compile @files
python keysurgeon.py selftest
python keysurgeon.py proof --json
```

If your change touches terminal UI, also check:

```powershell
keysurgeon --plain report
python -c "import app_textual; print(app_textual.build_app() is not None)"
```

## Privacy

Do not include typed private text in issues, fixtures, screenshots, or logs.
Reports should use key labels, timing metrics, verdicts, board model details,
and stack traces only.

## Conduct

Follow `CODE_OF_CONDUCT.md`. Keep issue and pull request threads specific,
evidence-based, and safe for people reporting keyboard faults.
