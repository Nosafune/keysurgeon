Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$targets = @(
    "__pycache__",
    "scripts\__pycache__",
    "dist",
    "build",
    "keysurgeon.egg-info",
    "keysurgeon.spec",
    ".runtime",
    "artifacts"
)

Push-Location $root
try {
    foreach ($target in $targets) {
        $resolved = Resolve-Path -LiteralPath $target -ErrorAction SilentlyContinue
        if (!$resolved) {
            continue
        }
        foreach ($item in $resolved) {
            $path = $item.Path
            if (!$path.StartsWith($root.Path, [System.StringComparison]::OrdinalIgnoreCase)) {
                throw "Refusing to remove outside project root: $path"
            }
            Remove-Item -LiteralPath $path -Recurse -Force
            Write-Host "removed $path"
        }
    }
    Write-Host "KEYSURGEON_CLEAN_ARTIFACTS_OK"
}
finally {
    Pop-Location
}
