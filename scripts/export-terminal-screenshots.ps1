Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$assets = Join-Path $root "site\assets"

$browser = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (!$browser) {
    throw "Chrome or Edge is required to export terminal demo screenshots."
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

function Get-SvgSize {
    param([string]$Path)
    $text = [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8)
    if ($text -notmatch 'viewBox="0 0 ([0-9.]+) ([0-9.]+)"') {
        throw "Could not read SVG viewBox: $Path"
    }
    $width = [Math]::Ceiling([double]$Matches[1])
    $height = [Math]::Ceiling([double]$Matches[2])
    return @($width, $height)
}

$shots = @(
    @{ Name = "rich"; Source = "keysurgeon-demo.svg"; Target = "keysurgeon-demo.png"; MinBytes = 50000 },
    @{ Name = "textual"; Source = "keysurgeon-app.svg"; Target = "keysurgeon-app.png"; MinBytes = 100000 }
)

foreach ($shot in $shots) {
    $source = Join-Path $assets $shot.Source
    $target = Join-Path $assets $shot.Target
    if (!(Test-Path -LiteralPath $source)) {
        throw "Missing terminal demo SVG: $source"
    }
    $size = Get-SvgSize -Path $source
    $uri = (New-Object System.Uri($source)).AbsoluteUri
    Invoke-HiddenBrowser "terminal demo screenshot $($shot.Name)" ($quietBrowserArgs + @("--window-size=$($size[0]),$($size[1])", "--screenshot=$target", $uri))
    $item = Get-Item -LiteralPath $target
    if ($item.Length -lt $shot.MinBytes) {
        throw "Terminal demo screenshot is unexpectedly small: $($item.FullName) $($item.Length) bytes"
    }
    Write-Host "KEYSURGEON_TERMINAL_SCREENSHOT_OK $($shot.Name) $($item.Length) bytes"
}
