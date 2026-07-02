param(
    [string]$DistRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$sourceRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
if (!$DistRoot) {
    $mirrorName = "keysurgeon" + "_dist"
    $DistRoot = Join-Path $sourceRoot.Path ("..\" + $mirrorName)
}
$distPath = Resolve-Path -LiteralPath $DistRoot

$ignoredPathRegexes = @(
    '(^|[\\/])\.git([\\/]|$)',
    '(^|[\\/])dist([\\/]|$)',
    '(^|[\\/])build([\\/]|$)',
    '(^|[\\/])\.runtime([\\/]|$)',
    '(^|[\\/])artifacts([\\/]|$)',
    '(^|[\\/])__pycache__([\\/]|$)',
    '(^|[\\/])[^\\/]+\.egg-info([\\/]|$)'
)
$ignoredFileRegexes = @(
    '\.py[co]$',
    '\.log$',
    'keysurgeon\.spec$',
    '(^|/)keysurgeon_profile\.json$',
    '(^|/)keysurgeon_boards\.json$',
    '(^|/)keysurgeon_watch\.json$',
    '(^|/)keysurgeon_watch\.pid$',
    '(^|/)keysurgeon_watch\.stop$',
    '(^|/)[Cc][Ll][Aa][Uu][Dd][Ee]\.md$',
    '(^|/)[Aa][Gg][Ee][Nn][Tt][Ss]\.md$',
    '(^|/)[Rr][Ee][Ff][Ee][Rr][Ee][Nn][Cc][Ee]\.md$'
)

function Convert-ToRelativePath {
    param(
        [string]$Root,
        [string]$Path
    )
    $fullRoot = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\', '/')
    $fullPath = (Resolve-Path -LiteralPath $Path).Path
    if (!$fullPath.StartsWith($fullRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside root: $Path"
    }
    return $fullPath.Substring($fullRoot.Length).TrimStart('\', '/') -replace '\\', '/'
}

function Test-Ignored {
    param([string]$RelativePath)
    foreach ($pattern in $ignoredPathRegexes) {
        if ($RelativePath -match $pattern) {
            return $true
        }
    }
    foreach ($pattern in $ignoredFileRegexes) {
        if ($RelativePath -match $pattern) {
            return $true
        }
    }
    return $false
}

function Get-PublicFiles {
    param([string]$Root)
    $files = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -LiteralPath $Root -Recurse -File -Force | ForEach-Object {
        $relative = Convert-ToRelativePath -Root $Root -Path $_.FullName
        if (!(Test-Ignored -RelativePath $relative)) {
            $files.Add($relative) | Out-Null
        }
    }
    return @($files.ToArray() | Sort-Object)
}

$sourceFiles = Get-PublicFiles -Root $sourceRoot.Path
$distFiles = Get-PublicFiles -Root $distPath.Path

$sourceSet = @{}
foreach ($file in $sourceFiles) { $sourceSet[$file] = $true }
$distSet = @{}
foreach ($file in $distFiles) { $distSet[$file] = $true }

$missing = @($sourceFiles | Where-Object { !$distSet.ContainsKey($_) })
$extra = @($distFiles | Where-Object { !$sourceSet.ContainsKey($_) })
$changed = New-Object System.Collections.Generic.List[string]

foreach ($file in $sourceFiles) {
    if (!$distSet.ContainsKey($file)) {
        continue
    }
    $sourceFile = Join-Path $sourceRoot.Path ($file -replace '/', '\')
    $distFile = Join-Path $distPath.Path ($file -replace '/', '\')
    $sourceHash = (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash
    $distHash = (Get-FileHash -LiteralPath $distFile -Algorithm SHA256).Hash
    if ($sourceHash -ne $distHash) {
        $changed.Add($file) | Out-Null
    }
}

if ($missing.Count -or $extra.Count -or $changed.Count) {
    Write-Host "KEYSURGEON_DIST_PARITY_FAIL"
    if ($missing.Count) {
        Write-Host "missing_in_dist:"
        foreach ($file in $missing) { Write-Host "- $file" }
    }
    if ($extra.Count) {
        Write-Host "extra_in_dist:"
        foreach ($file in $extra) { Write-Host "- $file" }
    }
    if ($changed.Count) {
        Write-Host "hash_mismatch:"
        foreach ($file in $changed) { Write-Host "- $file" }
    }
    exit 1
}

Write-Host "KEYSURGEON_DIST_PARITY_OK $($sourceFiles.Count)"
