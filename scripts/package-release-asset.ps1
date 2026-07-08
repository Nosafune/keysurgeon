Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$version = "0.2.1"
$releaseDir = Join-Path $root "dist\release"
$assetName = "keysurgeon-v$version-windows-x64.exe"
$assetPath = Join-Path $releaseDir $assetName
$notesSource = Join-Path $root "docs\RELEASE_NOTES_0.2.1.md"
$notesTarget = Join-Path $releaseDir "RELEASE_NOTES_0.2.1.md"
$proofSource = Join-Path $root "site\assets\keysurgeon-proof.json"
$checksumsPath = Join-Path $releaseDir "SHA256SUMS.txt"
$manifestPath = Join-Path $releaseDir "release-manifest.json"

function Invoke-Native {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

Push-Location $root
try {
    & (Join-Path $PSScriptRoot "build-exe.ps1")

    $exe = Join-Path $root "dist\keysurgeon.exe"
    if (!(Test-Path -LiteralPath $exe)) {
        throw "Missing built executable: $exe"
    }
    if (!(Test-Path -LiteralPath $notesSource)) {
        throw "Missing release notes: $notesSource"
    }
    if (!(Test-Path -LiteralPath $proofSource)) {
        throw "Missing public proof manifest: $proofSource"
    }

    New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
    Copy-Item -LiteralPath $exe -Destination $assetPath -Force
    Copy-Item -LiteralPath $notesSource -Destination $notesTarget -Force

    Invoke-Native "release asset version smoke" { & $assetPath --version | Out-Null }
    Invoke-Native "release asset doctor smoke" { & $assetPath --plain doctor | Out-Null }
    Invoke-Native "release asset export smoke" { & $assetPath export --json | Out-Null }
    $proofText = & $assetPath proof --json
    if ($LASTEXITCODE -ne 0) { throw "$assetName proof --json failed." }
    $proofSnapshot = $proofText | ConvertFrom-Json
    Invoke-Native "release asset selftest smoke" { & $assetPath selftest | Out-Null }

    $asset = Get-Item -LiteralPath $assetPath
    if ($asset.Length -lt 10000000) {
        throw "Release executable is unexpectedly small: $($asset.Length) bytes"
    }

    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $assetPath).Hash.ToLowerInvariant()
    $proofFile = Get-Item -LiteralPath $proofSource
    $proofHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $proofSource).Hash.ToLowerInvariant()
    "$hash  $assetName" | Set-Content -LiteralPath $checksumsPath -Encoding utf8

    $manifest = [ordered]@{
        name = "KeySurgeon"
        version = $version
        built_utc = [DateTimeOffset]::UtcNow.ToString("o")
        asset = [ordered]@{
            file = $assetName
            bytes = $asset.Length
            sha256 = $hash
        }
        public_demo_proof = [ordered]@{
            file = "site/assets/keysurgeon-proof.json"
            bytes = $proofFile.Length
            sha256 = $proofHash
        }
        proof_snapshot = [ordered]@{
            version = $proofSnapshot.version
            demo_assets = $proofSnapshot.local_proof.demo_assets.status
            manual_keyboard_smoke = $proofSnapshot.local_proof.manual_keyboard_smoke.status
            rich_textual_stack = $proofSnapshot.local_proof.rich_textual_stack.status
            public_blockers = $proofSnapshot.public_blockers
        }
        smoke = @(
            "$assetName --version",
            "$assetName --plain doctor",
            "$assetName export --json",
            "$assetName proof --json",
            "$assetName selftest"
        )
        notes = "RELEASE_NOTES_0.2.1.md"
    }
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8

    $manifestCheck = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($manifestCheck.public_demo_proof.sha256 -ne $proofHash) {
        throw "Release manifest proof hash mismatch."
    }
    if ($manifestCheck.proof_snapshot.demo_assets -ne "ok") {
        throw "Release manifest proof snapshot does not record ok demo assets."
    }
    if ($manifestCheck.proof_snapshot.manual_keyboard_smoke -eq "ok") {
        throw "Release manifest unexpectedly claims manual keyboard smoke is ok."
    }

    Write-Host "KEYSURGEON_RELEASE_ASSET_OK $assetPath $($asset.Length) bytes"
    Write-Host "KEYSURGEON_RELEASE_ASSET_SHA256 $hash"
    Write-Host "KEYSURGEON_RELEASE_PROOF_SHA256 $proofHash"
}
finally {
    Pop-Location
}
