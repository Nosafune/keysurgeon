Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
Push-Location $root
try {
    python .\scripts\render-demo-svg.py
    python .\scripts\render-app-svg.py
    python .\scripts\render-flow-svg.py
    & (Join-Path $PSScriptRoot "export-social-preview.ps1")
    & (Join-Path $PSScriptRoot "export-terminal-screenshots.ps1")
    & (Join-Path $PSScriptRoot "export-landing-screenshots.ps1")
    python .\scripts\render-proof-manifest.py

    $demo = Get-Item -LiteralPath "site\assets\keysurgeon-demo.svg"
    $demoPng = Get-Item -LiteralPath "site\assets\keysurgeon-demo.png"
    $app = Get-Item -LiteralPath "site\assets\keysurgeon-app.svg"
    $appPng = Get-Item -LiteralPath "site\assets\keysurgeon-app.png"
    $flow = Get-Item -LiteralPath "site\assets\keysurgeon-flow.svg"
    $social = Get-Item -LiteralPath "site\assets\keysurgeon-social.png"
    $landingDesktop = Get-Item -LiteralPath "site\assets\keysurgeon-landing-desktop.png"
    $landingMobile = Get-Item -LiteralPath "site\assets\keysurgeon-landing-mobile.png"
    $proof = Get-Item -LiteralPath "site\assets\keysurgeon-proof.json"
    if ($demo.Length -lt 10000) {
        throw "Demo SVG is unexpectedly small: $($demo.Length) bytes"
    }
    if ($app.Length -lt 10000) {
        throw "App SVG is unexpectedly small: $($app.Length) bytes"
    }
    if ($demoPng.Length -lt 50000) {
        throw "Demo PNG is unexpectedly small: $($demoPng.Length) bytes"
    }
    if ($appPng.Length -lt 100000) {
        throw "App PNG is unexpectedly small: $($appPng.Length) bytes"
    }
    if ($flow.Length -lt 5000) {
        throw "Flow SVG is unexpectedly small: $($flow.Length) bytes"
    }
    $flowText = Get-Content -LiteralPath $flow.FullName -Raw
    foreach ($sentinel in @("keysurgeon watch", "keysurgeon test E", "keysurgeon fix E", "keysurgeon proof --json")) {
        if ($flowText -notmatch [regex]::Escape($sentinel)) {
            throw "Flow SVG missing sentinel: $sentinel"
        }
    }
    if ($social.Length -lt 10000) {
        throw "Social preview PNG is unexpectedly small: $($social.Length) bytes"
    }
    if ($landingDesktop.Length -lt 100000) {
        throw "Landing desktop screenshot is unexpectedly small: $($landingDesktop.Length) bytes"
    }
    if ($landingMobile.Length -lt 50000) {
        throw "Landing mobile screenshot is unexpectedly small: $($landingMobile.Length) bytes"
    }
    if ($proof.Length -lt 1000) {
        throw "Proof manifest is unexpectedly small: $($proof.Length) bytes"
    }
    python .\scripts\verify-proof-manifest.py

    Write-Host "KEYSURGEON_DEMO_ASSETS_OK"
}
finally {
    Pop-Location
}
