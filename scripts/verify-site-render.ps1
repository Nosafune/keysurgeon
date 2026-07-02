Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$site = Join-Path $root "site\index.html"
$outDir = Join-Path $root ".runtime\site-smoke"

if (!(Test-Path -LiteralPath $site)) {
    throw "Missing site entrypoint: $site"
}

$browser = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (!$browser) {
    throw "Chrome or Edge is required for site render smoke."
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

New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$uri = "file:///" + ($site -replace "\\", "/") + "?rev=" + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$shots = @(
    @{ Name = "desktop"; Size = "1440,1200"; MinBytes = 70000 },
    @{ Name = "phone"; Size = "390,844"; MinBytes = 50000 },
    @{ Name = "mobile"; Size = "390,1800"; MinBytes = 50000 }
)

foreach ($shot in $shots) {
    $path = Join-Path $outDir "keysurgeon-landing-$($shot.Name).png"
    Invoke-HiddenBrowser "site render screenshot $($shot.Name)" ($quietBrowserArgs + @("--window-size=$($shot.Size)", "--screenshot=$path", $uri))
    if (!(Test-Path -LiteralPath $path)) {
        throw "Site screenshot was not written: $path"
    }
    $item = Get-Item -LiteralPath $path
    if ($item.Length -lt $shot.MinBytes) {
        throw "Site screenshot is unexpectedly small: $($item.FullName) $($item.Length) bytes"
    }
    Write-Host "SITE_SCREENSHOT_OK $($shot.Name) $($item.Length) bytes"
}

$html = Get-Content -LiteralPath $site -Raw
foreach ($needle in @("See install steps", "Windows", "MIT", "local JSON", "Rich + Textual", "See the signal", "--plain fallback", "Sample diagnosis copy", "keysurgeon ready", "keysurgeon proof --json", "assets/keysurgeon-flow.svg", "workflow, Rich, and Textual proof", "Install from the checkout today", "python -m pip install .", "post-publish path")) {
    if ($html -notlike "*$needle*") {
        throw "Missing landing copy: $needle"
    }
}

Write-Host "KEYSURGEON_SITE_RENDER_OK"
