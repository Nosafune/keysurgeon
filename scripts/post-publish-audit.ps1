param(
    [string]$Repo = "nosafune/keysurgeon",
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$expectedDescription = "Keyboard chatter diagnostic for Windows: catch double-typing, dead keys, and repair-first faults in a Rich/Textual terminal app."
$expectedTopics = @(
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
$expectedLabels = @(
    "bug",
    "board-data",
    "enhancement",
    "hardware-smoke",
    "good first issue",
    "help wanted"
)
$expectedIssues = @(
    "[board-data]: add conservative repair hint for a known board",
    "[docs]: clarify Windows install friction before first selftest",
    "[docs]: make one repair ladder phrase clearer",
    "[test]: cover one fault, export, proof, or UI state",
    "[hardware-smoke]: record real keyboard smoke for one install path"
)
$expectedAsset = "keysurgeon-v0.2.0-windows-x64.exe"
$expectedTag = "v0.2.0"

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
        return [pscustomobject]@{
            ExitCode = $LASTEXITCODE
            Output = ($output -join "`n")
        }
    }
    catch {
        return [pscustomobject]@{
            ExitCode = 1
            Output = ""
        }
    }
}

function ConvertFrom-OptionalJson {
    param([string]$Text)
    if (-not $Text) {
        return $null
    }
    try {
        return $Text | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

$repoResult = Invoke-OptionalNative {
    gh repo view $Repo --json description,homepageUrl,hasIssuesEnabled,repositoryTopics,url,defaultBranchRef,latestRelease
}
$repoData = ConvertFrom-OptionalJson $repoResult.Output
if ($repoResult.ExitCode -eq 0 -and $repoData) {
    Add-Result "ok" "GitHub repository" $repoData.url
    if ($repoData.description -eq $expectedDescription) {
        Add-Result "ok" "repository description" "matches launch positioning"
    } else {
        Add-Failure "repository description" "expected published KeySurgeon description"
    }
    if ($repoData.hasIssuesEnabled) {
        Add-Result "ok" "issue intake" "issues enabled"
    } else {
        Add-Failure "issue intake" "issues are not enabled"
    }
    $topicNames = @($repoData.repositoryTopics | ForEach-Object { $_.name })
    $missingTopics = @($expectedTopics | Where-Object { $_ -notin $topicNames })
    if ($missingTopics.Count -eq 0) {
        Add-Result "ok" "repository topics" "$($expectedTopics.Count) topics"
    } else {
        Add-Failure "repository topics" "missing: $($missingTopics -join ', ')"
    }
    if ($repoData.homepageUrl) {
        Add-Result "ok" "repository homepage" $repoData.homepageUrl
    } else {
        Add-Failure "repository homepage" "homepage URL is empty"
    }
} else {
    Add-Failure "GitHub repository" "gh could not view $Repo"
    Add-Failure "repository description" "repository metadata unavailable"
    Add-Failure "issue intake" "repository metadata unavailable"
    Add-Failure "repository topics" "repository metadata unavailable"
    Add-Failure "repository homepage" "repository metadata unavailable"
}

$labelResult = Invoke-OptionalNative {
    gh label list --repo $Repo --json name,color,description --limit 100
}
$labelData = ConvertFrom-OptionalJson $labelResult.Output
if ($labelResult.ExitCode -eq 0 -and $labelData) {
    $labelNames = @($labelData | ForEach-Object { $_.name })
    $missingLabels = @($expectedLabels | Where-Object { $_ -notin $labelNames })
    if ($missingLabels.Count -eq 0) {
        Add-Result "ok" "repository labels" "$($expectedLabels.Count) labels"
    } else {
        Add-Failure "repository labels" "missing: $($missingLabels -join ', ')"
    }
} else {
    Add-Failure "repository labels" "gh label list returned no labels"
}

$issueResult = Invoke-OptionalNative {
    gh issue list --repo $Repo --state all --json title,labels --limit 100
}
$issueData = ConvertFrom-OptionalJson $issueResult.Output
if ($issueResult.ExitCode -eq 0 -and $issueData) {
    $issueTitles = @($issueData | ForEach-Object { $_.title })
    $missingIssues = @($expectedIssues | Where-Object { $_ -notin $issueTitles })
    if ($missingIssues.Count -eq 0) {
        Add-Result "ok" "starter issues" "$($expectedIssues.Count) issues"
    } else {
        Add-Failure "starter issues" "missing: $($missingIssues -join '; ')"
    }
} else {
    Add-Failure "starter issues" "gh issue list returned no issues"
}

$selftestResult = Invoke-OptionalNative {
    gh run list --repo $Repo --workflow selftest.yml --limit 1 --json conclusion,status,databaseId
}
$selftestData = ConvertFrom-OptionalJson $selftestResult.Output
if ($selftestResult.ExitCode -eq 0 -and $selftestData -and $selftestData.Count -gt 0 -and $selftestData[0].conclusion -eq "success") {
    Add-Result "ok" "remote selftest workflow" "run $($selftestData[0].databaseId)"
} else {
    Add-Failure "remote selftest workflow" "latest selftest.yml run is not successful"
}

$pagesRunResult = Invoke-OptionalNative {
    gh run list --repo $Repo --workflow pages.yml --limit 1 --json conclusion,status,databaseId
}
$pagesRunData = ConvertFrom-OptionalJson $pagesRunResult.Output
if ($pagesRunResult.ExitCode -eq 0 -and $pagesRunData -and $pagesRunData.Count -gt 0 -and $pagesRunData[0].conclusion -eq "success") {
    Add-Result "ok" "remote pages workflow" "run $($pagesRunData[0].databaseId)"
} else {
    Add-Failure "remote pages workflow" "latest pages.yml run is not successful"
}

$pagesResult = Invoke-OptionalNative {
    gh api "repos/$Repo/pages"
}
$pagesData = ConvertFrom-OptionalJson $pagesResult.Output
if ($pagesResult.ExitCode -eq 0 -and $pagesData -and $pagesData.html_url) {
    Add-Result "ok" "GitHub Pages URL" $pagesData.html_url
} else {
    Add-Failure "GitHub Pages URL" "gh api repos/$Repo/pages returned no html_url"
}

$releaseResult = Invoke-OptionalNative {
    gh release view --repo $Repo --json tagName,name,assets,isDraft,isPrerelease
}
$releaseData = ConvertFrom-OptionalJson $releaseResult.Output
if ($releaseResult.ExitCode -eq 0 -and $releaseData) {
    $assets = @($releaseData.assets)
    $assetNames = @($assets | ForEach-Object { $_.name })
    if ($releaseData.tagName -ne $expectedTag) {
        Add-Failure "GitHub release" "expected $expectedTag, found $($releaseData.tagName)"
    } elseif ($releaseData.isDraft) {
        Add-Failure "GitHub release" "$($releaseData.tagName) is still a draft"
    } elseif ($releaseData.isPrerelease) {
        Add-Failure "GitHub release" "$($releaseData.tagName) is still a prerelease"
    } elseif ($expectedAsset -in $assetNames) {
        Add-Result "ok" "GitHub release asset" "$($releaseData.tagName) has $expectedAsset"
    } else {
        Add-Failure "GitHub release asset" "missing $expectedAsset"
    }
} else {
    Add-Failure "GitHub release asset" "no GitHub release visible"
}

if ($failures.Count) {
    if ($Json) {
        [pscustomobject]@{
            tool = "KeySurgeon"
            status = "blocked"
            repo = $Repo
            checks = @($checks.ToArray())
            failures = @($failures.ToArray())
        } | ConvertTo-Json -Depth 6
    } else {
        Write-Host ""
        Write-Host "KEYSURGEON_POST_PUBLISH_BLOCKED"
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
        repo = $Repo
        checks = @($checks.ToArray())
        failures = @()
    } | ConvertTo-Json -Depth 6
} else {
    Write-Host ""
    Write-Host "KEYSURGEON_POST_PUBLISH_READY"
}
