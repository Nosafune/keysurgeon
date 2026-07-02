Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$site = Join-Path $root "site\index.html"
$assets = Join-Path $root "site\assets"

if (!(Test-Path -LiteralPath $site)) {
    throw "Missing site entrypoint: $site"
}

$browser = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (!$browser) {
    throw "Chrome or Edge is required to export landing screenshots."
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

New-Item -ItemType Directory -Force -Path $assets | Out-Null
$uri = "file:///" + ($site -replace "\\", "/") + "?rev=" + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$shots = @(
    @{ Name = "desktop"; Size = "1440,1200"; MinBytes = 100000 },
    @{ Name = "mobile"; Size = "390,844"; MinBytes = 50000 }
)

foreach ($shot in $shots) {
    $path = Join-Path $assets "keysurgeon-landing-$($shot.Name).png"
    Invoke-HiddenBrowser "landing screenshot $($shot.Name)" ($quietBrowserArgs + @("--window-size=$($shot.Size)", "--screenshot=$path", $uri))
    Start-Sleep -Milliseconds 500
    if (!(Test-Path -LiteralPath $path)) {
        throw "Landing screenshot was not written: $path"
    }
    $item = Get-Item -LiteralPath $path
    if ($item.Length -lt $shot.MinBytes) {
        throw "Landing screenshot is unexpectedly small: $($item.FullName) $($item.Length) bytes"
    }
    Write-Host "KEYSURGEON_LANDING_SCREENSHOT_OK $($shot.Name) $($item.Length) bytes"
}
