param(
    [string]$Repo = "nosafune/keysurgeon",
    [string]$AuditPath = "",
    [string]$PostPublishAuditPath = "",
    [string]$ProofPath = "",
    [switch]$AsMarkdown,
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

function Invoke-CapturedNative {
    param([scriptblock]$Command)
    $output = & $Command 2>&1
    return [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Output = ($output -join "`n")
    }
}

function Read-JsonFile {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }
    $resolved = Resolve-Path -LiteralPath $Path
    return (Get-Content -LiteralPath $resolved -Raw | ConvertFrom-Json)
}

function Status-Icon {
    param([string]$Status)
    if ($Status -eq "ok" -or $Status -eq "ready") { return "ok" }
    if ($Status -eq "command-gated") { return "gate" }
    return "blocked"
}

Push-Location $root
try {
    $audit = Read-JsonFile $AuditPath
    if ($null -eq $audit) {
        $auditResult = Invoke-CapturedNative {
            & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "pre-publish-audit.ps1") -Json
        }
        if ($auditResult.ExitCode -notin @(0, 1)) {
            throw "pre-publish-audit.ps1 -Json failed with unexpected exit code $($auditResult.ExitCode)."
        }
        $audit = $auditResult.Output | ConvertFrom-Json
    }

    $postPublishAudit = Read-JsonFile $PostPublishAuditPath
    if ($null -eq $postPublishAudit) {
        $postPublishResult = Invoke-CapturedNative {
            & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "post-publish-audit.ps1") -Repo $Repo -Json
        }
        if ($postPublishResult.ExitCode -notin @(0, 1)) {
            throw "post-publish-audit.ps1 -Json failed with unexpected exit code $($postPublishResult.ExitCode)."
        }
        $postPublishAudit = $postPublishResult.Output | ConvertFrom-Json
    }

    $proof = Read-JsonFile $ProofPath
    if ($null -eq $proof) {
        $proofResult = Invoke-CapturedNative {
            python .\keysurgeon.py proof --json
        }
        if ($proofResult.ExitCode -ne 0) {
            throw "keysurgeon proof --json failed."
        }
        $proof = $proofResult.Output | ConvertFrom-Json
    }

    $proofSummary = $proof.proof_summary
    $checks = @($audit.checks)
    $failures = @($audit.failures)
    $postChecks = @($postPublishAudit.checks)
    $postFailures = @($postPublishAudit.failures)
    $okChecks = @($checks | Where-Object { $_.status -eq "ok" })
    $missingChecks = @($checks | Where-Object { $_.status -ne "ok" -and $_.status -ne "check" })
    $postOkChecks = @($postChecks | Where-Object { $_.status -eq "ok" })
    $postMissingChecks = @($postChecks | Where-Object { $_.status -ne "ok" -and $_.status -ne "check" })
    $next = @(
        @($failures + $postFailures) |
            ForEach-Object { $_ } |
            Select-Object -First 5
    )

    $board = [pscustomobject]@{
        tool = "KeySurgeon"
        repo = $Repo
        status = $audit.status
        mode = "local summary only; no git, GitHub, release, Pages, or deploy changes are made"
        post_publish_status = $postPublishAudit.status
        proof = [pscustomobject]@{
            local = $proofSummary.local
            command_gated = $proofSummary.command_gated
            blocked = $proofSummary.blocked
        }
        public_gates = [pscustomobject]@{
            ok = $okChecks.Count
            missing = $missingChecks.Count
        }
        post_publish_gates = [pscustomobject]@{
            ok = $postOkChecks.Count
            missing = $postMissingChecks.Count
        }
        blockers = $failures
        post_publish_blockers = $postFailures
        next_actions = $next
    }

    if ($Json) {
        $board | ConvertTo-Json -Depth 6
        exit 0
    }

    if ($AsMarkdown) {
        Write-Output "# KeySurgeon Launch Readiness"
        Write-Output ""
        Write-Output "- Repo: ``$Repo``"
        Write-Output "- Status: ``$($board.status)``"
        Write-Output "- Post-publish status: ``$($board.post_publish_status)``"
        Write-Output "- Mode: $($board.mode)"
        Write-Output "- Local proof: $($proofSummary.local) local / $($proofSummary.command_gated) command-gated / $($proofSummary.blocked) blocked"
        Write-Output "- Public gates: $($okChecks.Count) ok / $($missingChecks.Count) missing"
        Write-Output "- Post-publish gates: $($postOkChecks.Count) ok / $($postMissingChecks.Count) missing"
        Write-Output ""
        Write-Output "## Pre-Publish Gate Board"
        Write-Output ""
        foreach ($check in $checks) {
            if ($check.status -eq "check") { continue }
            Write-Output "- $(Status-Icon $check.status) ``$($check.name)`` - $($check.detail)"
        }
        Write-Output ""
        Write-Output "## Post-Publish Gate Board"
        Write-Output ""
        foreach ($check in $postChecks) {
            if ($check.status -eq "check") { continue }
            Write-Output "- $(Status-Icon $check.status) ``$($check.name)`` - $($check.detail)"
        }
        Write-Output ""
        Write-Output "## Next Actions"
        Write-Output ""
        if ($next.Count -eq 0) {
            Write-Output "- none; pre-publish and post-publish audits report ready"
        } else {
            foreach ($item in $next) {
                Write-Output "- $item"
            }
        }
        Write-Output ""
        Write-Output "KEYSURGEON_LAUNCH_READINESS_OK"
        exit 0
    }

    Write-Host "KEYSURGEON_LAUNCH_READINESS"
    Write-Host "repo: $Repo"
    Write-Host "status: $($board.status)"
    Write-Host "post_publish_status: $($board.post_publish_status)"
    Write-Host "mode: $($board.mode)"
    Write-Host "local_proof: $($proofSummary.local) local / $($proofSummary.command_gated) command-gated / $($proofSummary.blocked) blocked"
    Write-Host "public_gates: $($okChecks.Count) ok / $($missingChecks.Count) missing"
    Write-Host "post_publish_gates: $($postOkChecks.Count) ok / $($postMissingChecks.Count) missing"
    Write-Host ""
    Write-Host "pre-publish gate board:"
    foreach ($check in $checks) {
        if ($check.status -eq "check") { continue }
        Write-Host "- $(Status-Icon $check.status) $($check.name): $($check.detail)"
    }
    Write-Host ""
    Write-Host "post-publish gate board:"
    foreach ($check in $postChecks) {
        if ($check.status -eq "check") { continue }
        Write-Host "- $(Status-Icon $check.status) $($check.name): $($check.detail)"
    }
    Write-Host ""
    Write-Host "next actions:"
    if ($next.Count -eq 0) {
        Write-Host "- none; pre-publish and post-publish audits report ready"
    } else {
        foreach ($item in $next) {
            Write-Host "- $item"
        }
    }
    Write-Host "KEYSURGEON_LAUNCH_READINESS_OK"
}
finally {
    Pop-Location
}
