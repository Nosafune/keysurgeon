# Verify the public tree: selftest passes, no agent files, public assets exist.
# Every check propagates a real exit code — a crash here fails CI.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Invoke-Check {
    param([string]$Label, [scriptblock]$Body)
    Write-Host "== $Label"
    & $Body
    if ($LASTEXITCODE -ne 0) {
        Write-Error "FAILED: $Label (exit $LASTEXITCODE)"
        exit 1
    }
}

# 1. Full selftest (fault logic, privacy/export, UI renderers, CLI dispatch).
Invoke-Check "selftest" { python keysurgeon.py selftest }

# 2. Agent/internal files must not ship in the public tree.
$forbidden = @("CLAUDE.md", "AGENTS.md", "REFERENCE.md")
foreach ($name in $forbidden) {
    if (Test-Path (Join-Path $root $name)) {
        Write-Error "FAILED: internal file $name is present in the public tree"
        exit 1
    }
}
Write-Host "== no internal agent files"

# 3. Public site assets referenced by README/landing page must exist.
$assets = @(
    "site/index.html",
    "site/assets/keysurgeon.css",
    "site/assets/keysurgeon-wordmark.svg",
    "site/assets/keysurgeon-mark.svg",
    "site/assets/keysurgeon-demo.svg",
    "site/assets/keysurgeon-flow.svg",
    "site/assets/keysurgeon-demo.png",
    "site/assets/keysurgeon-app.png",
    "site/assets/keysurgeon-social.png",
    "site/assets/keysurgeon-landing-desktop.png",
    "site/assets/keysurgeon-landing-mobile.png",
    "site/assets/keysurgeon-proof.json"
)
foreach ($rel in $assets) {
    if (-not (Test-Path (Join-Path $root $rel))) {
        Write-Error "FAILED: missing public asset $rel"
        exit 1
    }
}
Write-Host "== public assets present"

# 4. Demo asset provenance manifest matches the committed assets.
Invoke-Check "proof manifest" { python scripts/verify-proof-manifest.py }

Write-Host "PUBLIC_TREE_OK"
exit 0
