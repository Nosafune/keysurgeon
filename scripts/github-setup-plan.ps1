param(
    [string]$Repo = "nosafune/keysurgeon",
    [switch]$AsMarkdown
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$description = "Keyboard chatter diagnostic for Windows: catch double-typing, dead keys, and repair-first faults in a Rich/Textual terminal app."
$homepageNote = "Set homepage only after the manual pages workflow passes and the URL resolves."
$socialPreview = "site/assets/keysurgeon-social.png"
$repoName = ($Repo -split "/")[-1]
$topics = @(
    "keyboard",
    "keyboard-tester",
    "keyboard-diagnostics",
    "keyboard-chatter",
    "keyboard-repair",
    "double-typing",
    "dead-keys",
    "debounce",
    "mechanical-keyboard",
    "usb-hid",
    "hardware-diagnostics",
    "windows",
    "cli",
    "rich",
    "textual",
    "repair"
)

$labels = @(
    @{ Name = "bug"; Color = "ff5a4d"; Description = "Confirmed or suspected KeySurgeon defect." },
    @{ Name = "board-data"; Color = "00d7e6"; Description = "Keyboard model, VID/PID, or board repair metadata." },
    @{ Name = "enhancement"; Color = "41d982"; Description = "Scoped diagnostic, workflow, packaging, app, docs, or repair-guide improvement." },
    @{ Name = "hardware-smoke"; Color = "f5b83d"; Description = "Real Windows keyboard smoke evidence for release gating." },
    @{ Name = "good first issue"; Color = "7057ff"; Description = "Small, evidence-backed starter task with clear local proof." },
    @{ Name = "help wanted"; Color = "008672"; Description = "Maintainer-approved contribution lane for board data, docs, tests, or smoke evidence." }
)

function Quote-Arg {
    param([string]$Value)
    return '"' + ($Value -replace '"', '\"') + '"'
}

function Command-Line {
    param([string]$Text)
    if ($AsMarkdown) {
        return "    $Text"
    }
    return $Text
}

if ($AsMarkdown) {
    Write-Output "# KeySurgeon GitHub Setup Plan"
    Write-Output ""
    Write-Output "Repo: ``$Repo``"
    Write-Output ""
    Write-Output "> Dry-run only. This script prints commands and does not call ``gh``."
    Write-Output ""
    Write-Output "## Commands"
    Write-Output ""
}
else {
    Write-Output "KEYSURGEON_GITHUB_SETUP_PLAN"
    Write-Output "repo: $Repo"
    Write-Output "mode: dry-run only; no gh commands are executed"
    Write-Output ""
}

Write-Output (Command-Line "# If the repository does not exist yet, create it only after explicit approval:")
Write-Output (Command-Line "gh repo create $Repo --public --description $(Quote-Arg $description) --disable-wiki --clone=false")
Write-Output (Command-Line "# If the repository already exists, start here:")
Write-Output (Command-Line "gh repo edit $Repo --description $(Quote-Arg $description) --enable-issues=true")
Write-Output (Command-Line "gh repo edit $Repo --add-topic $($topics -join ',')")
foreach ($label in $labels) {
    Write-Output (Command-Line "gh label create $(Quote-Arg $label.Name) --repo $Repo --color $($label.Color) --description $(Quote-Arg $label.Description) --force")
}

if ($AsMarkdown) {
    Write-Output ""
    Write-Output "## Manual Steps"
    Write-Output ""
    Write-Output "- Upload ``$socialPreview`` as the repository social preview."
    Write-Output "- $homepageNote"
    Write-Output "- Use the create command only if ``$repoName`` does not already exist. Otherwise start from ``gh repo edit``."
    Write-Output "- Do not add a CI badge until the remote self-test workflow has a green run."
    Write-Output "- Do not claim release assets until the GitHub release asset is attached and smoke-tested."
}
else {
    Write-Output ""
    Write-Output "manual:"
    Write-Output "- upload $socialPreview as the repository social preview"
    Write-Output "- $homepageNote"
    Write-Output "- use the create command only if $repoName does not already exist; otherwise start from gh repo edit"
    Write-Output "- do not add a CI badge until the remote self-test workflow has a green run"
    Write-Output "- do not claim release assets until the GitHub release asset is attached and smoke-tested"
    Write-Output ""
    Write-Output "KEYSURGEON_GITHUB_SETUP_PLAN_OK $($topics.Count) topics $($labels.Count) labels"
}
