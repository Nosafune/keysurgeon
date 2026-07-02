Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$artifactPatterns = @(
    "dist/",
    "build/",
    "*.egg-info/",
    "keysurgeon.spec",
    ".runtime/",
    "artifacts/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.log"
)
$artifactRegexes = @(
    '(^|/)dist(/|$)',
    '(^|/)build(/|$)',
    '(^|/)[^/]+\.egg-info(/|$)',
    '(^|/)keysurgeon\.spec$',
    '(^|/)\.runtime(/|$)',
    '(^|/)artifacts(/|$)',
    '(^|/)__pycache__(/|$)',
    '\.py[co]$',
    '\.log$'
)

function Quote-Arg {
    param([string]$Value)
    return '"' + ($Value -replace '"', '\"') + '"'
}

$gitRoot = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or !$gitRoot) {
    throw "Could not resolve git root."
}

$mirrorName = "keysurgeon" + "_dist"
$mirrorRoot = Join-Path $root.Path ("..\" + $mirrorName)
$mirrorStatus = "absent"
$mirrorDetail = "adjacent distribution mirror not found"

Push-Location $root
try {
    if (Test-Path -LiteralPath $mirrorRoot) {
        $parityOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "verify-dist-parity.ps1") 2>&1
        if ($LASTEXITCODE -eq 0) {
            $mirrorStatus = "parity-ok"
            $mirrorDetail = ($parityOutput -join " ").Trim()
        } else {
            $mirrorStatus = "parity-failed"
            $mirrorDetail = ($parityOutput -join " ").Trim()
        }
    }

    $status = & git -C $gitRoot status --porcelain -- $root.Path
    if ($LASTEXITCODE -ne 0) {
        throw "git status failed."
    }

    $entries = @($status | Where-Object { $_.Trim() })
    $blocked = New-Object System.Collections.Generic.List[string]
    $candidates = New-Object System.Collections.Generic.List[string]

    foreach ($entry in $entries) {
        if ($entry.Length -lt 4) {
            continue
        }
        $path = $entry.Substring(3).Trim()
        if ($path -match ' -> ') {
            $path = ($path -split ' -> ')[-1].Trim()
        }
        $normalized = $path -replace '\\', '/'
        $isArtifact = $false
        foreach ($pattern in $artifactRegexes) {
            if ($normalized -match $pattern) {
                $isArtifact = $true
                break
            }
        }
        if ($isArtifact) {
            $blocked.Add($path) | Out-Null
        } else {
            $candidates.Add($path) | Out-Null
        }
    }

    Write-Host "KEYSURGEON_RELEASE_COMMIT_PLAN"
    Write-Host "mode: dry-run only; no git add or git commit is executed"
    Write-Host "git_root: $gitRoot"
    Write-Host "project_root: $($root.Path)"
    Write-Host "changed: $($entries.Count)"
    Write-Host "candidates: $($candidates.Count)"
    Write-Host "blocked_artifacts: $($blocked.Count)"
    Write-Host "distribution_mirror: $mirrorStatus"
    Write-Host "distribution_mirror_detail: $mirrorDetail"
    Write-Host "distribution_mirror_scope: not included in the source commit command; verify parity and publish/copy it only after explicit approval"
    Write-Host ""

    if ($mirrorStatus -eq "parity-failed") {
        throw "Distribution mirror parity failed. Run scripts/verify-dist-parity.ps1 and mirror source changes before committing."
    }

    if ($blocked.Count -gt 0) {
        Write-Host "blocked artifacts:"
        foreach ($path in $blocked) {
            Write-Host "- $path"
        }
        throw "Release commit plan found generated artifacts. Run scripts/clean-artifacts.ps1 before committing."
    }

    if ($candidates.Count -eq 0) {
        Write-Host "No release files need committing."
        Write-Host "KEYSURGEON_RELEASE_COMMIT_PLAN_OK 0"
        return
    }

    Write-Host "candidate files:"
    foreach ($path in $candidates) {
        Write-Host "- $path"
    }
    Write-Host ""
    Write-Host "review, then commit only after explicit approval:"
    Write-Host ("git -C {0} add --" -f (Quote-Arg $gitRoot))
    foreach ($path in $candidates) {
        Write-Host ("  {0}" -f (Quote-Arg $path))
    }
    Write-Host ('git -C {0} commit -m "Prepare KeySurgeon v0.2.0 public release"' -f (Quote-Arg $gitRoot))
    Write-Host ""
    Write-Host "artifact guards:"
    foreach ($pattern in $artifactPatterns) {
        Write-Host "- $pattern"
    }
    Write-Host "KEYSURGEON_RELEASE_COMMIT_PLAN_OK $($candidates.Count)"
}
finally {
    Pop-Location
}
