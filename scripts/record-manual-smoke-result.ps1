param(
    [ValidateSet("hardware-smoke-pass", "hardware-smoke-partial", "hardware-smoke-fail", "not-run")]
    [string]$Result,
    [string]$Tester = "",
    [string]$Keyboard = "",
    [string]$InstallSource = "",
    [string]$EvidenceReport = "",
    [string]$Notes = "",
    [string]$Out = "docs\MANUAL_SMOKE_RESULT.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Result)) {
    throw "Missing -Result. Use hardware-smoke-pass, hardware-smoke-partial, hardware-smoke-fail, or not-run."
}

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$outPath = Join-Path $root $Out

function Assert-CompletedEvidenceReport {
    param([string]$Path)

    $text = Get-Content -LiteralPath $Path -Raw
    $required = @(
        "## Results",
        "| Version prints expected release |",
        "| Selftest passes |",
        "| Doctor reports environment |",
        '| `test E` captures the key label |',
        "| Watch background starts |",
        "| No typed private text is stored |"
    )
    $missing = @($required | Where-Object { -not $text.Contains($_) })
    if ($missing.Count -gt 0) {
        throw "Evidence report is missing required manual-smoke sections: $($missing -join ', ')"
    }

    if ($text -match '(?m)^\|\s*[^|]+\s*\|\s*\|\s*\|') {
        throw "Evidence report still has blank Pass/Fail and Evidence table cells."
    }

    if ($text.Contains("Keyboard brand/model:`n- Keyboard type:") -or $text.Contains("Keyboard brand/model:`r`n- Keyboard type:")) {
        throw "Evidence report must include a keyboard brand/model before recording hardware-smoke-pass."
    }

    if ($text.Contains("local checkout / GitHub install / executable artifact")) {
        throw "Evidence report still contains the install-source placeholder."
    }

    if ($text -notmatch 'hardware-smoke-pass') {
        throw "Evidence report must record hardware-smoke-pass before the gate file can be marked pass."
    }
}

if ($Result -eq "hardware-smoke-pass") {
    if ([string]::IsNullOrWhiteSpace($EvidenceReport)) {
        throw "hardware-smoke-pass requires -EvidenceReport pointing to the completed manual smoke report."
    }
    $evidencePath = Join-Path $root $EvidenceReport
    if (!(Test-Path -LiteralPath $evidencePath)) {
        throw "Evidence report not found: $EvidenceReport"
    }
    Assert-CompletedEvidenceReport $evidencePath
}

$date = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
$body = @"
# Manual Smoke Result

Status: ``$Result``

This file records the latest real-keyboard smoke result for release gating.
Do not mark ``hardware-smoke-pass`` until ``docs/MANUAL_KEYBOARD_SMOKE.md`` or
``scripts/manual-keyboard-smoke.ps1`` has been completed on a real Windows
keyboard.

## Latest Result

- Date: $date
- Tester: $Tester
- Keyboard: $Keyboard
- Install source: $InstallSource
- Result: ``$Result``
- Evidence report: $EvidenceReport

Valid result values:

- ``hardware-smoke-pass``: hook path and watcher behavior passed on real hardware.
- ``hardware-smoke-partial``: some behavior passed, but gaps remain.
- ``hardware-smoke-fail``: do not claim real hardware behavior yet.
- ``not-run``: no current real-keyboard proof.

Notes:
$Notes
"@

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outPath) | Out-Null
$body | Set-Content -LiteralPath $outPath -Encoding utf8
Write-Host "KEYSURGEON_MANUAL_SMOKE_RESULT_RECORDED $Result $outPath"
