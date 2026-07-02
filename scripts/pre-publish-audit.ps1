param(
    [string]$Owner = "nosafune",
    [string]$Repo = "keysurgeon",
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$repoSlug = "$Owner/$Repo"
$failures = New-Object System.Collections.Generic.List[string]
$checks = New-Object System.Collections.Generic.List[object]

function Add-Result {
    param(
        [string]$Status,
        [string]$Name,
        [string]$Detail = ""
    )
    $checks.Add([pscustomobject]@{
        status = $Status
        name = $Name
        detail = $Detail
    }) | Out-Null
    if ($Json) {
        return
    }
    $line = "{0,-7} {1}" -f $Status, $Name
    if ($Detail) {
        $line = "$line - $Detail"
    }
    Write-Host $line
}

function Add-Failure {
    param([string]$Name, [string]$Detail)
    Add-Result "missing" $Name $Detail
    $failures.Add("${Name}: $Detail") | Out-Null
}

function Invoke-OptionalNative {
    param([scriptblock]$Command)
    try {
        $output = & $Command 2>$null
        return @{
            ExitCode = $LASTEXITCODE
            Output = ($output -join "`n")
        }
    }
    catch {
        return @{
            ExitCode = 1
            Output = ""
        }
    }
}

Push-Location $root
try {
    Add-Result "check" "local public tree" "scripts/verify-public-tree.ps1"
    if ($Json) {
        $publicTreeResult = Invoke-OptionalNative {
            & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "verify-public-tree.ps1")
        }
        if ($publicTreeResult.ExitCode -eq 0) {
            Add-Result "ok" "local public tree" "KEYSURGEON_PUBLIC_TREE_OK"
        } else {
            Add-Failure "local public tree" "scripts/verify-public-tree.ps1 failed"
        }
    } else {
        & (Join-Path $PSScriptRoot "verify-public-tree.ps1")
        Add-Result "ok" "local public tree"
    }

    $releaseStateResult = Invoke-OptionalNative { git status --porcelain -- . }
    if ($releaseStateResult.ExitCode -eq 0) {
        $releaseChanges = @($releaseStateResult.Output -split "`n" | Where-Object { $_.Trim() })
        if ($releaseChanges.Count -eq 0) {
            Add-Result "ok" "release files committed" "KeySurgeon source tree is clean"
        } else {
            $plan = "run scripts/release-commit-plan.ps1 for the dry-run candidate list"
            Add-Failure "release files committed" "$($releaseChanges.Count) local tracked/untracked change(s) under KeySurgeon; $plan"
        }
    } else {
        Add-Failure "release files committed" "git status could not inspect KeySurgeon source tree"
    }

    $manualSmoke = Join-Path $root "docs\MANUAL_SMOKE_RESULT.md"
    if (Test-Path -LiteralPath $manualSmoke) {
        $manualSmokeText = Get-Content -LiteralPath $manualSmoke -Raw
        if ($manualSmokeText -match 'Result:\s*`?hardware-smoke-pass`?') {
            Add-Result "ok" "manual keyboard smoke" "hardware-smoke-pass recorded"
        } else {
            Add-Failure "manual keyboard smoke" "docs/MANUAL_SMOKE_RESULT.md is not hardware-smoke-pass"
        }
    } else {
        Add-Failure "manual keyboard smoke" "docs/MANUAL_SMOKE_RESULT.md missing"
    }

    $remoteResult = Invoke-OptionalNative { git remote get-url origin }
    if ($remoteResult.ExitCode -eq 0 -and $remoteResult.Output) {
        Add-Result "ok" "git remote origin" $remoteResult.Output.Trim()
    } else {
        Add-Failure "git remote origin" "no origin configured"
    }

    $repoResult = Invoke-OptionalNative { gh repo view $repoSlug --json name,url,defaultBranchRef,latestRelease }
    if ($repoResult.ExitCode -eq 0 -and $repoResult.Output) {
        $repoData = $repoResult.Output | ConvertFrom-Json
        Add-Result "ok" "GitHub repository" $repoData.url
        if ($repoData.latestRelease) {
            Add-Result "ok" "latest release" $repoData.latestRelease.name
        } else {
            Add-Failure "latest release" "no GitHub release found"
        }
    } else {
        Add-Failure "GitHub repository" "gh could not view $repoSlug"
        Add-Failure "latest release" "no GitHub release found (repository missing)"
    }

    $releaseAssetResult = Invoke-OptionalNative { gh release view --repo $repoSlug --json tagName,name,assets,isDraft,isPrerelease }
    if ($releaseAssetResult.ExitCode -eq 0 -and $releaseAssetResult.Output) {
        $releaseData = $releaseAssetResult.Output | ConvertFrom-Json
        $assets = @($releaseData.assets)
        if ($assets.Count -gt 0) {
            Add-Result "ok" "GitHub release asset" "$($releaseData.tagName) has $($assets.Count) asset(s)"
        } else {
            Add-Failure "GitHub release asset" "$($releaseData.tagName) has no attached assets"
        }
    } else {
        Add-Failure "GitHub release asset" "no GitHub release asset visible"
    }

    $selftestResult = Invoke-OptionalNative { gh run list --repo $repoSlug --workflow selftest.yml --limit 1 --json conclusion,status,databaseId }
    if ($selftestResult.ExitCode -eq 0 -and $selftestResult.Output) {
        $runs = $selftestResult.Output | ConvertFrom-Json
        if ($runs.Count -gt 0 -and $runs[0].conclusion -eq "success") {
            Add-Result "ok" "remote selftest workflow" "run $($runs[0].databaseId)"
        } else {
            Add-Failure "remote selftest workflow" "no successful latest run"
        }
    } else {
        Add-Failure "remote selftest workflow" "no remote workflow run visible"
    }

    $pagesResult = Invoke-OptionalNative { gh run list --repo $repoSlug --workflow pages.yml --limit 1 --json conclusion,status,databaseId }
    if ($pagesResult.ExitCode -eq 0 -and $pagesResult.Output) {
        $runs = $pagesResult.Output | ConvertFrom-Json
        if ($runs.Count -gt 0 -and $runs[0].conclusion -eq "success") {
            Add-Result "ok" "remote pages workflow" "run $($runs[0].databaseId)"
        } else {
            Add-Failure "remote pages workflow" "no successful latest run"
        }
    } else {
        Add-Failure "remote pages workflow" "no remote Pages run visible"
    }

    if ($failures.Count) {
        if ($Json) {
            [pscustomobject]@{
                tool = "KeySurgeon"
                status = "blocked"
                repo = $repoSlug
                checks = @($checks.ToArray())
                failures = @($failures.ToArray())
            } | ConvertTo-Json -Depth 6
        } else {
            Write-Host ""
            Write-Host "KEYSURGEON_PRE_PUBLISH_BLOCKED"
            foreach ($failure in $failures) {
                Write-Host "- $failure"
            }
        }
        exit 1
    }

    if ($Json) {
        [pscustomobject]@{
            tool = "KeySurgeon"
            status = "ready"
            repo = $repoSlug
            checks = @($checks.ToArray())
            failures = @()
        } | ConvertTo-Json -Depth 6
    } else {
        Write-Host ""
        Write-Host "KEYSURGEON_PRE_PUBLISH_READY"
    }
}
finally {
    Pop-Location
}
