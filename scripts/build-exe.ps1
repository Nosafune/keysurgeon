Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

function Invoke-Native {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

Push-Location $root
try {
    Invoke-Native "install pyinstaller" { python -m pip install "pyinstaller>=6.14,<7" }
    Invoke-Native "build executable" { python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --console `
        --name keysurgeon `
        --add-data "pyproject.toml;." `
        --add-data "scripts\release-check.ps1;scripts" `
        --add-data "site;site" `
        --add-data "docs\MANUAL_SMOKE_RESULT.md;docs" `
        --add-data "docs\PROOF_MATRIX.md;docs" `
        --hidden-import rich_ui `
        --hidden-import app_textual `
        --hidden-import doctor `
        --hidden-import export_report `
        --hidden-import issue_packet `
        --hidden-import manual_smoke `
        --hidden-import proof_report `
        --hidden-import ks_profile `
        keysurgeon.py }
    Invoke-Native "exe version smoke" { & (Join-Path $root "dist\keysurgeon.exe") --version }
    Invoke-Native "exe doctor smoke" { & (Join-Path $root "dist\keysurgeon.exe") --plain doctor }
    Invoke-Native "exe issue packet smoke" { & (Join-Path $root "dist\keysurgeon.exe") issue --out (Join-Path $root ".runtime\exe-issue\KEYSURGEON_ISSUE_PACKET.md") }
    Invoke-Native "exe export smoke" { & (Join-Path $root "dist\keysurgeon.exe") export --json }
    Invoke-Native "exe proof smoke" { & (Join-Path $root "dist\keysurgeon.exe") proof --json }
    Invoke-Native "exe manual smoke scaffold" { & (Join-Path $root "dist\keysurgeon.exe") smoke --out (Join-Path $root ".runtime\exe-smoke\MANUAL_SMOKE_REPORT.md") }
    Invoke-Native "exe selftest smoke" { & (Join-Path $root "dist\keysurgeon.exe") selftest }
    Write-Host "KEYSURGEON_EXE_BUILD_OK"
}
finally {
    Pop-Location
}
