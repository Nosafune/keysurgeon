param(
    [string]$Repo = "nosafune/keysurgeon",
    [switch]$AsMarkdown
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$issues = @(
    @{
        Title = "[board-data]: add conservative repair hint for a known board"
        Labels = @("board-data", "good first issue", "help wanted")
        Body = @'
## What this improves

KeySurgeon can give a better repair ladder when it recognizes one more real board model.

## Evidence to add

- Brand/model:
- External, laptop, or unknown:
- Mechanical, membrane, or unknown:
- Hot-swap, soldered, or unknown:
- VID/PID if available:
- Source for the board facts:

## Guardrails

- Do not infer hot-swap support from USB vendor ID alone.
- If the source is weak, use a conservative hint and keep asking the user to confirm.
- Do not add typed private text, screenshots of typed text, or telemetry.

## Done

- `boards.py` contains the conservative board hint.
- `python keysurgeon.py selftest` passes.
- The hint does not overpromise repairability.
'@
    },
    @{
        Title = "[docs]: clarify Windows install friction before first selftest"
        Labels = @("enhancement", "good first issue", "help wanted")
        Body = @'
## Problem

A Windows install path is confusing or fails before the first `keysurgeon selftest`.

## Evidence

- Windows version:
- Shell:
- Python command used:
- `python --version`:
- Non-private error text:

## Desired outcome

The README or diagnosis guide should make the next command obvious without claiming the future GitHub install path works before publish.

## Done

- The install note preserves the current local-checkout path until public proof exists.
- `.\scripts\verify-public-tree.ps1` passes.
- No private paths, tokens, or typed text are added.
'@
    },
    @{
        Title = "[docs]: make one repair ladder phrase clearer"
        Labels = @("enhancement", "good first issue")
        Body = @'
## Confusing wording

Quote the current sentence or output line that is unclear.

## Better wording

Suggest a plain-language replacement that keeps replacement as the last rung.

## Context

- Fault:
- Board type:
- Why the current wording could mislead someone:

## Done

- The wording is cheapest-first: software filter, debris, contact clean, switch work, replacement last.
- It does not promise a repair KeySurgeon cannot apply itself.
- `python keysurgeon.py selftest` passes.
'@
    },
    @{
        Title = "[test]: cover one fault, export, proof, or UI state"
        Labels = @("enhancement", "good first issue")
        Body = @'
## Behavior to lock down

Describe the small behavior that should not regress.

## Suggested proof

- Synthetic event sample, saved profile state, or parser case:
- Expected verdict/output:

## Done

- The test uses synthetic events or local sample state.
- No real typed text is added to fixtures or logs.
- `python keysurgeon.py selftest` passes.
'@
    },
    @{
        Title = "[hardware-smoke]: record real keyboard smoke for one install path"
        Labels = @("hardware-smoke", "help wanted")
        Body = @'
## Scope

Record real Windows keyboard evidence for one install path or release artifact. This issue should not claim broad hardware proof until the linked smoke result is complete.

## Evidence

- Install source:
- Keyboard brand/model:
- Tester:
- Date:
- Commands run:
  - `keysurgeon selftest`
  - `keysurgeon doctor`
  - `keysurgeon test [key]`
  - `keysurgeon smoke`
- Result file or report:

## Done

- `docs/MANUAL_SMOKE_RESULT.md` records `hardware-smoke-pass` only after the real interactive test passes.
- Private typed text is not included.
- `.\scripts\pre-publish-audit.ps1` no longer blocks on manual hardware smoke.
'@
    }
)

function Quote-Arg {
    param([string]$Value)
    return '"' + ($Value -replace '"', '\"') + '"'
}

function One-Line {
    param([string]$Text)
    return (($Text -replace "`r?`n", "\n") -replace '"', '\"')
}

function Command-Line {
    param([string]$Text)
    if ($AsMarkdown) {
        return "    $Text"
    }
    return $Text
}

if ($AsMarkdown) {
    Write-Output "# KeySurgeon Starter Issue Seed Plan"
    Write-Output ""
    Write-Output "Repo: ``$Repo``"
    Write-Output ""
    Write-Output "> Dry-run only. This script prints ``gh issue create`` commands and does not call ``gh``."
    Write-Output ""
    Write-Output "Create repository labels first with ``.\scripts\github-setup-plan.ps1``."
    Write-Output ""
    Write-Output "## Commands"
    Write-Output ""
}
else {
    Write-Output "KEYSURGEON_STARTER_ISSUES_PLAN"
    Write-Output "repo: $Repo"
    Write-Output "mode: dry-run only; no gh commands are executed"
    Write-Output ""
}

foreach ($issue in $issues) {
    $labels = $issue.Labels -join ","
    $body = One-Line $issue.Body
    Write-Output (Command-Line "gh issue create --repo $Repo --title $(Quote-Arg $issue.Title) --label $(Quote-Arg $labels) --body $(Quote-Arg $body)")
}

if ($AsMarkdown) {
    Write-Output ""
    Write-Output "## Guardrails"
    Write-Output ""
    Write-Output "- Seed these only after the repository exists, labels exist, and issue intake is enabled."
    Write-Output "- Do not seed remote proof, release asset, or Pages claims before those surfaces pass."
    Write-Output "- Keep typed private text out of issue bodies and attachments."
}
else {
    Write-Output ""
    Write-Output "guardrails:"
    Write-Output "- seed only after repository, labels, and issue intake exist"
    Write-Output "- do not seed remote proof, release asset, or Pages claims before those surfaces pass"
    Write-Output "- keep typed private text out of issue bodies and attachments"
    Write-Output ""
    Write-Output "KEYSURGEON_STARTER_ISSUES_PLAN_OK $($issues.Count) issues"
}
