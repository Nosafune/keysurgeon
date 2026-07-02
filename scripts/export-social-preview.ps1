Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$svg = Join-Path $root "site\assets\keysurgeon-social.svg"
$png = Join-Path $root "site\assets\keysurgeon-social.png"

if (!(Test-Path -LiteralPath $svg)) {
    throw "Missing source SVG: $svg"
}

$browser = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (!$browser) {
    throw "Chrome or Edge is required to export the social preview PNG."
}

$quietBrowserArgs = @(
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--hide-scrollbars",
    "--disable-background-networking",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-first-run-ui",
    "--no-first-run",
    "--no-default-browser-check"
)

function Invoke-HiddenBrowser {
    param(
        [string]$Name,
        [string[]]$ArgumentList
    )
    $stamp = [System.Guid]::NewGuid().ToString("N")
    $outPath = Join-Path ([System.IO.Path]::GetTempPath()) "keysurgeon-browser-$stamp.out"
    $errPath = Join-Path ([System.IO.Path]::GetTempPath()) "keysurgeon-browser-$stamp.err"
    $profilePath = Join-Path ([System.IO.Path]::GetTempPath()) "keysurgeon-browser-profile-$stamp"
    New-Item -ItemType Directory -Force -Path $profilePath | Out-Null
    $run = Start-Process `
        -FilePath $browser `
        -ArgumentList (@("--user-data-dir=$profilePath") + $ArgumentList) `
        -WindowStyle Hidden `
        -RedirectStandardOutput $outPath `
        -RedirectStandardError $errPath `
        -Wait `
        -PassThru
    $errText = if (Test-Path -LiteralPath $errPath) { Get-Content -LiteralPath $errPath -Raw } else { "" }
    Remove-Item -LiteralPath $outPath, $errPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $profilePath -Recurse -Force -ErrorAction SilentlyContinue
    if ($run.ExitCode -ne 0) {
        throw "$Name failed with exit code $($run.ExitCode). $errText"
    }
}

$uri = "file:///" + ($svg -replace "\\", "/") + "?rev=" + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
Invoke-HiddenBrowser "social preview screenshot" ($quietBrowserArgs + @("--window-size=1280,640", "--screenshot=$png", $uri))
Start-Sleep -Milliseconds 500

if (!(Test-Path -LiteralPath $png)) {
    throw "Social preview PNG was not written: $png"
}

$item = Get-Item -LiteralPath $png
if ($item.Length -lt 10000) {
    throw "Social preview PNG is unexpectedly small: $($item.Length) bytes"
}

Write-Host "KEYSURGEON_SOCIAL_PREVIEW_OK $($item.FullName) $($item.Length) bytes"
