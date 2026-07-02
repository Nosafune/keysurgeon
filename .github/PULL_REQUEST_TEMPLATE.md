# Pull Request

## What Changed

- 

## Evidence

Paste the relevant local checks:

```powershell
python keysurgeon.py selftest
python keysurgeon.py proof --json
.\scripts\verify-public-tree.ps1
```

For UI, landing page, packaging, or release-doc changes, include the matching
script output such as `.\scripts\verify-site-render.ps1` or
`.\scripts\release-check.ps1`.

## Privacy And Scope

- [ ] No typed private text, credentials, tokens, or full key logs are included.
- [ ] The change does not claim real hardware proof unless manual smoke evidence
      records `hardware-smoke-pass`.
- [ ] The change does not claim GitHub release, CI, Pages, or executable proof
      unless the remote evidence exists.
- [ ] The change is scoped to KeySurgeon behavior, docs, packaging, or public
      presentation.

## Notes

-
