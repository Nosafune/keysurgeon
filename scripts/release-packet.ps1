param(
    [string]$Repo = "nosafune/keysurgeon",
    [string]$OutDir = "artifacts\release-packet"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

function Invoke-CapturedNative {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    $output = & $Command 2>&1
    return [pscustomobject]@{
        Name = $Name
        ExitCode = $LASTEXITCODE
        Output = ($output -join "`n")
    }
}

function Write-Utf8 {
    param(
        [string]$Path,
        [string]$Text
    )
    $Text | Set-Content -LiteralPath $Path -Encoding utf8
}

Push-Location $root
try {
    $outPath = Join-Path $root $OutDir
    New-Item -ItemType Directory -Path $outPath -Force | Out-Null

    $audit = Invoke-CapturedNative "pre-publish audit json" {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "pre-publish-audit.ps1") -Json
    }
    if ($audit.ExitCode -notin @(0, 1)) {
        throw "pre-publish-audit.ps1 -Json failed with unexpected exit code $($audit.ExitCode)."
    }
    $auditData = $audit.Output | ConvertFrom-Json
    $auditPath = Join-Path $outPath "pre-publish-audit.json"
    Write-Utf8 $auditPath $audit.Output

    $commitPlan = Invoke-CapturedNative "release commit plan" {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "release-commit-plan.ps1")
    }
    if ($commitPlan.ExitCode -ne 0) {
        throw "release-commit-plan.ps1 failed; clean generated artifacts before building the packet."
    }
    $commitPlanPath = Join-Path $outPath "release-commit-plan.txt"
    Write-Utf8 $commitPlanPath $commitPlan.Output

    $setupPlan = Invoke-CapturedNative "github setup plan" {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "github-setup-plan.ps1") -Repo $Repo -AsMarkdown
    }
    if ($setupPlan.ExitCode -ne 0) {
        throw "github-setup-plan.ps1 failed."
    }
    $setupPlanPath = Join-Path $outPath "github-setup-plan.md"
    Write-Utf8 $setupPlanPath $setupPlan.Output

    $starterPlan = Invoke-CapturedNative "starter issue seed plan" {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "seed-starter-issues-plan.ps1") -Repo $Repo -AsMarkdown
    }
    if ($starterPlan.ExitCode -ne 0) {
        throw "seed-starter-issues-plan.ps1 failed."
    }
    $starterPlanPath = Join-Path $outPath "starter-issues-plan.md"
    Write-Utf8 $starterPlanPath $starterPlan.Output

    $proof = Invoke-CapturedNative "proof json" {
        python .\keysurgeon.py proof --json
    }
    if ($proof.ExitCode -ne 0) {
        throw "keysurgeon proof --json failed."
    }
    $proofData = $proof.Output | ConvertFrom-Json
    $proofPath = Join-Path $outPath "proof.json"
    Write-Utf8 $proofPath $proof.Output

    $postPublish = Invoke-CapturedNative "post-publish audit json" {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "post-publish-audit.ps1") -Repo $Repo -Json
    }
    if ($postPublish.ExitCode -notin @(0, 1)) {
        throw "post-publish-audit.ps1 -Json failed with unexpected exit code $($postPublish.ExitCode)."
    }
    $postPublishPath = Join-Path $outPath "post-publish-audit.json"
    Write-Utf8 $postPublishPath $postPublish.Output

    $readiness = Invoke-CapturedNative "launch readiness board" {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "launch-readiness.ps1") -Repo $Repo -AuditPath $auditPath -PostPublishAuditPath $postPublishPath -ProofPath $proofPath -AsMarkdown
    }
    if ($readiness.ExitCode -ne 0) {
        throw "launch-readiness.ps1 failed."
    }
    $readinessPath = Join-Path $outPath "launch-readiness.md"
    Write-Utf8 $readinessPath $readiness.Output

    $launchCopy = Get-Content -LiteralPath "docs\LAUNCH_PACKET.md" -Raw
    $launchCopyPath = Join-Path $outPath "launch-copy.md"
    Write-Utf8 $launchCopyPath $launchCopy

    $assetManifest = Get-Content -LiteralPath "site\assets\keysurgeon-proof.json" -Raw
    $assetManifestPath = Join-Path $outPath "public-asset-proof.json"
    Write-Utf8 $assetManifestPath $assetManifest

    $failures = @($auditData.failures)
    $proofSummary = $proofData.proof_summary
    $summary = @(
        "# KeySurgeon v0.2.0 Release Packet",
        "",
        "Generated: $(Get-Date -Format s)",
        "Repo target: ``$Repo``",
        "Mode: local dry-run only; no git, GitHub, release, Pages, or deploy changes were made.",
        "",
        "## Status",
        "",
        "- pre-publish audit: ``$($auditData.status)``",
        "- local proof: $($proofSummary.local) local / $($proofSummary.command_gated) command-gated / $($proofSummary.blocked) blocked",
        "- release commit plan: dry-run candidate list generated",
        "- GitHub setup plan: dry-run commands generated",
        "- starter issue plan: dry-run issue commands generated",
        "- launch readiness board: local summary generated",
        "- post-publish audit: read-only remote proof snapshot generated",
        "",
        "## Blocking Gates",
        ""
    )
    if ($failures.Count -eq 0) {
        $summary += "- none reported by ``pre-publish-audit.ps1 -Json``"
    } else {
        foreach ($failure in $failures) {
            $summary += "- $failure"
        }
    }
    $summary += @(
        "",
        "## Packet Files",
        "",
        "- ``pre-publish-audit.json`` - machine-readable publish gate state",
        "- ``release-commit-plan.txt`` - dry-run scoped commit candidate list",
        "- ``github-setup-plan.md`` - repository description, topics, labels, and manual social-preview steps",
        "- ``starter-issues-plan.md`` - dry-run starter issue commands for early public contribution lanes",
        "- ``proof.json`` - local proof matrix and honest blockers",
        "- ``launch-readiness.md`` - one-page local launch board from audit and proof JSON",
        "- ``post-publish-audit.json`` - read-only post-publish repository, workflow, Pages, and release proof",
        "- ``public-asset-proof.json`` - public asset provenance and hashes",
        "- ``launch-copy.md`` - launch copy and social posting guardrails",
        "",
        "## Guardrails",
        "",
        "- Do not claim a public repository, Pages homepage, release asset, CI badge, or executable download until the matching remote proof exists.",
        "- Do not claim broad hardware proof until the manual real-keyboard smoke result records ``hardware-smoke-pass``.",
        "- Do not seed starter issues until the repository, labels, and issue intake exist.",
        "- After publish, run ``.\scripts\post-publish-audit.ps1`` before claiming public visibility is complete.",
        "- Run ``.\scripts\clean-artifacts.ps1`` after inspection if the packet is no longer needed locally.",
        "",
        "KEYSURGEON_RELEASE_PACKET_OK"
    )
    $summaryPath = Join-Path $outPath "README.md"
    Write-Utf8 $summaryPath ($summary -join "`n")

    Write-Host "KEYSURGEON_RELEASE_PACKET"
    Write-Host "out_dir: $outPath"
    Write-Host "status: $($auditData.status)"
    Write-Host "files: 10"
    Write-Host "KEYSURGEON_RELEASE_PACKET_OK"
}
finally {
    Pop-Location
}
