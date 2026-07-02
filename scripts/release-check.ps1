Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
Push-Location $root
try {
    $files = Get-ChildItem -Filter *.py -File | ForEach-Object { $_.FullName }
    python -m py_compile @files
    python keysurgeon.py selftest
    python keysurgeon.py --version
    python keysurgeon.py --plain doctor
    python keysurgeon.py export --json
    python keysurgeon.py proof --json
    python -c "import app_textual; print('TEXTUAL_FACTORY_OK', app_textual.build_app() is not None)"
    Remove-Item -LiteralPath "dist" -Recurse -Force -ErrorAction SilentlyContinue
    $wheelStamp = [System.Guid]::NewGuid().ToString("N")
    $wheelOutPath = Join-Path ([System.IO.Path]::GetTempPath()) "keysurgeon-wheel-$wheelStamp.out"
    $wheelErrPath = Join-Path ([System.IO.Path]::GetTempPath()) "keysurgeon-wheel-$wheelStamp.err"
    $wheelRun = Start-Process `
        -FilePath "python" `
        -ArgumentList @("-m", "pip", "wheel", ".", "--no-deps", "--wheel-dir", "dist") `
        -WindowStyle Hidden `
        -RedirectStandardOutput $wheelOutPath `
        -RedirectStandardError $wheelErrPath `
        -Wait `
        -PassThru
    $wheelOut = if (Test-Path -LiteralPath $wheelOutPath) { Get-Content -LiteralPath $wheelOutPath -Raw } else { "" }
    $wheelErr = if (Test-Path -LiteralPath $wheelErrPath) { Get-Content -LiteralPath $wheelErrPath -Raw } else { "" }
    Remove-Item -LiteralPath $wheelOutPath, $wheelErrPath -Force -ErrorAction SilentlyContinue
    if ($wheelOut) {
        Write-Host $wheelOut.TrimEnd()
    }
    if ($wheelErr) {
        Write-Host $wheelErr.TrimEnd()
    }
    if ($wheelRun.ExitCode -ne 0) {
        throw "pip wheel failed with exit code $($wheelRun.ExitCode)."
    }
    $wheelText = "$wheelOut`n$wheelErr"
    if ($wheelText -match "License classifiers are deprecated|project\.license[\s\S]*deprecated") {
        throw "Package metadata emitted deprecated license warnings."
    }
    if ($wheelText -match "SetuptoolsDeprecationWarning") {
        throw "Package metadata emitted an unexpected SetuptoolsDeprecationWarning."
    }
    Write-Host "WHEEL_LICENSE_WARNINGS_CLEAN"
    python -c "import pathlib, zipfile; wheels=list(pathlib.Path('dist').glob('keysurgeon-*.whl')); assert wheels, 'missing wheel'; names=zipfile.ZipFile(wheels[-1]).namelist(); assert 'export_report.py' in names and 'proof_report.py' in names, names; print('WHEEL_EXPORT_REPORT_OK', wheels[-1].name)"
    Write-Host "KEYSURGEON_RELEASE_CHECK_OK"
}
finally {
    Pop-Location
}
