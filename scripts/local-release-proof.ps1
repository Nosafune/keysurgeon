param(
    [switch]$KeepArtifacts
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$auditLog = Join-Path $root ".runtime\local-release-proof\pre-publish-audit.log"
$auditErr = Join-Path $root ".runtime\local-release-proof\pre-publish-audit.err.log"
$postPublishLog = Join-Path $root ".runtime\local-release-proof\post-publish-audit.log"
$postPublishErr = Join-Path $root ".runtime\local-release-proof\post-publish-audit.err.log"

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    Write-Host ""
    Write-Host "== $Name =="
    & $Command
}

Push-Location $root
try {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $auditLog) | Out-Null

    Invoke-Step "demo assets" {
        & (Join-Path $PSScriptRoot "generate-demo-assets.ps1")
    }

    Invoke-Step "landing render" {
        & (Join-Path $PSScriptRoot "verify-site-render.ps1")
    }

    Invoke-Step "public tree" {
        & (Join-Path $PSScriptRoot "verify-public-tree.ps1")
    }

    Invoke-Step "release asset package" {
        & (Join-Path $PSScriptRoot "package-release-asset.ps1")
    }

    Invoke-Step "pre-publish audit" {
        $auditProcess = Start-Process `
            -FilePath "powershell" `
            -ArgumentList @(
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                (Join-Path $PSScriptRoot "pre-publish-audit.ps1")
            ) `
            -Wait `
            -PassThru `
            -WindowStyle Hidden `
            -RedirectStandardOutput $auditLog `
            -RedirectStandardError $auditErr
        $auditCode = $auditProcess.ExitCode
        Get-Content -LiteralPath $auditLog
        if ((Test-Path -LiteralPath $auditErr) -and (Get-Item -LiteralPath $auditErr).Length -gt 0) {
            Get-Content -LiteralPath $auditErr
        }
        if ($auditCode -eq 0) {
            if ((Get-Content -LiteralPath $auditLog -Raw) -notmatch "KEYSURGEON_PRE_PUBLISH_READY") {
                throw "Pre-publish audit exited 0 without KEYSURGEON_PRE_PUBLISH_READY."
            }
        }
        elseif ($auditCode -eq 1) {
            $auditText = Get-Content -LiteralPath $auditLog -Raw
            if ($auditText -notmatch "KEYSURGEON_PRE_PUBLISH_BLOCKED") {
                throw "Pre-publish audit exited 1 without KEYSURGEON_PRE_PUBLISH_BLOCKED."
            }
            foreach ($expected in @(
                "release files committed",
                "manual keyboard smoke",
                "git remote origin",
                "GitHub repository",
                "latest release",
                "GitHub release asset",
                "remote selftest workflow",
                "remote pages workflow"
            )) {
                if ($auditText -notmatch [regex]::Escape($expected)) {
                    throw "Pre-publish audit blocked on unexpected/missing gate: $expected"
                }
            }
            Write-Host "KEYSURGEON_REMOTE_GATES_BLOCKED_EXPECTED"
        }
        else {
            throw "Pre-publish audit failed with exit code $auditCode."
        }
    }

    Invoke-Step "post-publish audit" {
        $postPublishProcess = Start-Process `
            -FilePath "powershell" `
            -ArgumentList @(
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                (Join-Path $PSScriptRoot "post-publish-audit.ps1")
            ) `
            -Wait `
            -PassThru `
            -WindowStyle Hidden `
            -RedirectStandardOutput $postPublishLog `
            -RedirectStandardError $postPublishErr
        $postPublishCode = $postPublishProcess.ExitCode
        Get-Content -LiteralPath $postPublishLog
        if ((Test-Path -LiteralPath $postPublishErr) -and (Get-Item -LiteralPath $postPublishErr).Length -gt 0) {
            Get-Content -LiteralPath $postPublishErr
        }
        if ($postPublishCode -eq 0) {
            if ((Get-Content -LiteralPath $postPublishLog -Raw) -notmatch "KEYSURGEON_POST_PUBLISH_READY") {
                throw "Post-publish audit exited 0 without KEYSURGEON_POST_PUBLISH_READY."
            }
        }
        elseif ($postPublishCode -eq 1) {
            $postPublishText = Get-Content -LiteralPath $postPublishLog -Raw
            if ($postPublishText -notmatch "KEYSURGEON_POST_PUBLISH_BLOCKED") {
                throw "Post-publish audit exited 1 without KEYSURGEON_POST_PUBLISH_BLOCKED."
            }
            foreach ($expected in @(
                "GitHub repository",
                "repository description",
                "issue intake",
                "repository topics",
                "repository homepage",
                "repository labels",
                "starter issues",
                "remote selftest workflow",
                "remote pages workflow",
                "GitHub Pages URL",
                "GitHub release asset"
            )) {
                if ($postPublishText -notmatch [regex]::Escape($expected)) {
                    throw "Post-publish audit blocked on unexpected/missing gate: $expected"
                }
            }
            Write-Host "KEYSURGEON_POST_PUBLISH_GATES_BLOCKED_EXPECTED"
        }
        else {
            throw "Post-publish audit failed with exit code $postPublishCode."
        }
    }

    Write-Host ""
    Write-Host "KEYSURGEON_LOCAL_RELEASE_PROOF_OK"
}
finally {
    Pop-Location
    if (!$KeepArtifacts) {
        & (Join-Path $PSScriptRoot "clean-artifacts.ps1")
    }
}
