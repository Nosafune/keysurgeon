Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$samples = @(
    "Result: ``hardware-smoke-pass``",
    "- Result: ``hardware-smoke-pass``",
    "Result: hardware-smoke-pass"
)

foreach ($sample in $samples) {
    if ($sample -notmatch 'Result:\s*`?hardware-smoke-pass`?') {
        throw "Manual smoke pass regex did not match sample: $sample"
    }
}

$misses = @(
    "Result: ``hardware-smoke-partial``",
    "Result: ``hardware-smoke-fail``",
    "Result: ``not-run``"
)

foreach ($sample in $misses) {
    if ($sample -match 'Result:\s*`?hardware-smoke-pass`?') {
        throw "Manual smoke pass regex matched non-pass sample: $sample"
    }
}

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$runtime = Join-Path $root ".runtime\manual-smoke-gate-test"
New-Item -ItemType Directory -Force -Path $runtime | Out-Null

$blankReport = Join-Path $runtime "blank-report.md"
@"
# Manual Smoke Report

## Environment

- Keyboard brand/model:
- Keyboard type: unknown
- Install source: local checkout / GitHub install / executable artifact

## Results

| Check | Pass/Fail | Evidence |
|---|---|---|
| Version prints expected release |  |  |
| Selftest passes |  |  |
| Doctor reports environment |  |  |
| ``test E`` captures the key label |  |  |
| Watch background starts |  |  |
| No typed private text is stored |  |  |

## Release Claim

- ``hardware-smoke-pass``: hook path and watcher behavior passed on a real keyboard.
"@ | Set-Content -LiteralPath $blankReport -Encoding utf8

$blankOut = Join-Path $runtime "blank-result.md"
$hadNativeErrorPreference = Test-Path Variable:\PSNativeCommandUseErrorActionPreference
if ($hadNativeErrorPreference) {
    $previousNativeErrorPreference = $PSNativeCommandUseErrorActionPreference
}
$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$PSNativeCommandUseErrorActionPreference = $false
$blank = & powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\record-manual-smoke-result.ps1 -Result hardware-smoke-pass -EvidenceReport ".runtime\manual-smoke-gate-test\blank-report.md" -Out ".runtime\manual-smoke-gate-test\blank-result.md" 2>&1
$blankExit = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
if ($hadNativeErrorPreference) {
    $PSNativeCommandUseErrorActionPreference = $previousNativeErrorPreference
}
else {
    Remove-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue
}
if ($blankExit -eq 0) {
    throw "Recorder accepted an incomplete manual smoke scaffold as hardware-smoke-pass."
}
if (($blank -join "`n") -notmatch "blank Pass/Fail|keyboard brand/model|install-source placeholder") {
    throw "Recorder rejected blank scaffold with an unexpected message: $blank"
}

$completeReport = Join-Path $runtime "complete-report.md"
@"
# Manual Smoke Report

## Environment

- Keyboard brand/model: Test Board 1000
- Keyboard type: hot-swap mechanical
- Install source: local checkout

## Results

| Check | Pass/Fail | Evidence |
|---|---|---|
| Version prints expected release | Pass | ``0.2.0`` |
| Selftest passes | Pass | ``all checks passed`` |
| Doctor reports environment | Pass | ``doctor passed`` |
| ``test E`` captures the key label | Pass | ``E`` verdict captured |
| Watch background starts | Pass | watcher pid recorded |
| No typed private text is stored | Pass | export contains labels/timing only |

## Release Claim

``hardware-smoke-pass``
"@ | Set-Content -LiteralPath $completeReport -Encoding utf8

$completeOut = Join-Path $runtime "complete-result.md"
& powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\record-manual-smoke-result.ps1 -Result hardware-smoke-pass -EvidenceReport ".runtime\manual-smoke-gate-test\complete-report.md" -Tester "gate test" -Keyboard "Test Board 1000" -InstallSource "local checkout" -Out ".runtime\manual-smoke-gate-test\complete-result.md" | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "Recorder rejected completed manual smoke evidence."
}
if (-not (Test-Path -LiteralPath $completeOut)) {
    throw "Recorder did not write completed-result.md"
}

Write-Host "KEYSURGEON_MANUAL_SMOKE_GATE_TEST_OK"
