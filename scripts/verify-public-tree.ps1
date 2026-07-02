Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

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

function Invoke-IsolatedPowerShell {
    param(
        [string]$Name,
        [string]$ScriptPath
    )

    $stamp = [System.Guid]::NewGuid().ToString("N")
    $outPath = Join-Path ([System.IO.Path]::GetTempPath()) "keysurgeon-$stamp.out"
    $errPath = Join-Path ([System.IO.Path]::GetTempPath()) "keysurgeon-$stamp.err"
    $run = Start-Process `
        -FilePath "powershell" `
        -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $ScriptPath) `
        -WindowStyle Hidden `
        -RedirectStandardOutput $outPath `
        -RedirectStandardError $errPath `
        -Wait `
        -PassThru
    function Read-RedirectedText {
        param([string]$Path)
        if (!(Test-Path -LiteralPath $Path)) {
            return ""
        }
        for ($attempt = 0; $attempt -lt 10; $attempt++) {
            try {
                $stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
                try {
                    $reader = New-Object IO.StreamReader($stream, [Text.Encoding]::UTF8)
                    try {
                        return $reader.ReadToEnd()
                    }
                    finally {
                        $reader.Dispose()
                    }
                }
                finally {
                    $stream.Dispose()
                }
            }
            catch [IO.IOException] {
                Start-Sleep -Milliseconds 100
            }
        }
        throw "Could not read redirected output: $Path"
    }
    $outText = Read-RedirectedText $outPath
    $errText = Read-RedirectedText $errPath
    Remove-Item -LiteralPath $outPath, $errPath -Force -ErrorAction SilentlyContinue
    if ($outText) {
        Write-Host $outText.TrimEnd()
    }
    if ($errText) {
        Write-Host $errText.TrimEnd()
    }
    if ($run.ExitCode -ne 0) {
        throw "$Name failed with exit code $($run.ExitCode)."
    }
}

Push-Location $root
try {
    $required = @(
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "PRODUCT.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "SUPPORT.md",
        "pyproject.toml",
        "export_report.py",
        "proof_report.py",
        "scripts\clean-artifacts.ps1",
        "scripts\export-landing-screenshots.ps1",
        "scripts\export-terminal-screenshots.ps1",
        "scripts\generate-demo-assets.ps1",
        "scripts\github-setup-plan.ps1",
        "scripts\local-release-proof.ps1",
        "scripts\manual-keyboard-smoke.ps1",
        "scripts\package-release-asset.ps1",
        "scripts\record-manual-smoke-result.ps1",
        "scripts\render-demo-svg.py",
        "scripts\render-app-svg.py",
        "scripts\demo_svg_format.py",
        "scripts\render-flow-svg.py",
        "scripts\render-proof-manifest.py",
        "scripts\verify-proof-manifest.py",
        "scripts\verify-landing-metadata.py",
        "scripts\verify-public-scrub.py",
        "scripts\verify-workflow-policy.py",
        "scripts\verify-site-render.ps1",
        "scripts\pre-publish-audit.ps1",
        "scripts\post-publish-audit.ps1",
        "scripts\launch-readiness.ps1",
        "scripts\test-manual-smoke-gate.ps1",
        "scripts\verify-textual-app.py",
        ".github\workflows\selftest.yml",
        ".github\workflows\windows-exe.yml",
        ".github\workflows\pages.yml",
        ".github\PULL_REQUEST_TEMPLATE.md",
        ".github\ISSUE_TEMPLATE\config.yml",
        ".github\ISSUE_TEMPLATE\bug_report.yml",
        ".github\ISSUE_TEMPLATE\board_report.yml",
        ".github\ISSUE_TEMPLATE\feature_request.yml",
        ".github\ISSUE_TEMPLATE\manual_smoke_report.yml",
        "docs\DIAGNOSIS_GUIDE.md",
        "docs\FIRST_ISSUES.md",
        "docs\STARTER_ISSUE_TEMPLATES.md",
        "docs\KEYBOARD_TESTER_COMPARISON.md",
        "docs\ROADMAP.md",
        "docs\RELEASE_NOTES_0.2.0.md",
        "docs\RELEASE_CHECKLIST.md",
        "docs\PUBLISH_RUNBOOK.md",
        "docs\LAUNCH_PACKET.md",
        "docs\MANUAL_KEYBOARD_SMOKE.md",
        "docs\MANUAL_SMOKE_REPORT.md",
        "docs\MANUAL_SMOKE_RESULT.md",
        "docs\GITHUB_METADATA.md",
        "docs\GITHUB_LABELS.md",
        "docs\PROOF_MATRIX.md",
        "site\index.html",
        "site\assets\keysurgeon-mark.svg",
        "site\assets\keysurgeon-wordmark.svg",
        "site\assets\keysurgeon-app.svg",
        "site\assets\keysurgeon-app.png",
        "site\assets\keysurgeon-demo.svg",
        "site\assets\keysurgeon-demo.png",
        "site\assets\keysurgeon-flow.svg",
        "site\assets\keysurgeon-landing-desktop.png",
        "site\assets\keysurgeon-landing-mobile.png",
        "site\assets\keysurgeon-proof.json",
        "site\assets\keysurgeon-social.svg",
        "site\assets\keysurgeon-social.png"
    )

    foreach ($path in $required) {
        if (!(Test-Path -LiteralPath $path)) {
            throw "Missing required public file: $path"
        }
    }
    $ignoreText = Get-Content -LiteralPath ".gitignore" -Raw
    foreach ($pattern in @("dist/", "build/", "*.egg-info/", "keysurgeon.spec", "__pycache__/", "*.log")) {
        if ($ignoreText -notmatch [regex]::Escape($pattern)) {
            throw "Missing .gitignore pattern: $pattern"
        }
    }
    Write-Host "GITIGNORE_OK"

    Invoke-Native "yaml parse" { python -c "import yaml, pathlib; paths=list(pathlib.Path('.github/workflows').glob('*.yml'))+list(pathlib.Path('.github/ISSUE_TEMPLATE').glob('*.yml')); [yaml.safe_load(p.read_text(encoding='utf-8')) for p in paths]; print('YAML_PARSE_OK', len(paths))" }
    Invoke-Native "workflow policy" { python .\scripts\verify-workflow-policy.py }
    Invoke-Native "release check" { & (Join-Path $PSScriptRoot "release-check.ps1") }
    Invoke-Native "public assets" { python -c "from html.parser import HTMLParser; from pathlib import Path; import xml.etree.ElementTree as ET; HTMLParser().feed(Path('site/index.html').read_text(encoding='utf-8')); [ET.parse(str(x)) for x in Path('site/assets').glob('*.svg')]; p=Path('site/assets/keysurgeon-social.png'); desktop=Path('site/assets/keysurgeon-landing-desktop.png'); mobile=Path('site/assets/keysurgeon-landing-mobile.png'); demo=Path('site/assets/keysurgeon-demo.svg'); demo_png=Path('site/assets/keysurgeon-demo.png'); app=Path('site/assets/keysurgeon-app.svg'); app_png=Path('site/assets/keysurgeon-app.png'); flow=Path('site/assets/keysurgeon-flow.svg'); proof=Path('site/assets/keysurgeon-proof.json'); flow_text=flow.read_text(encoding='utf-8'); assert p.exists() and p.stat().st_size > 10000; assert desktop.exists() and desktop.stat().st_size > 100000; assert mobile.exists() and mobile.stat().st_size > 50000; assert demo.exists() and demo.stat().st_size > 10000; assert demo_png.exists() and demo_png.stat().st_size > 50000; assert app.exists() and app.stat().st_size > 10000; assert app_png.exists() and app_png.stat().st_size > 100000; assert flow.exists() and flow.stat().st_size > 5000; assert all(x in flow_text for x in ('keysurgeon watch','keysurgeon test E','keysurgeon fix E','keysurgeon ready','keysurgeon proof --json')); assert proof.exists() and proof.stat().st_size > 1000; print('PUBLIC_ASSETS_OK', p.stat().st_size, desktop.stat().st_size, mobile.stat().st_size, demo_png.stat().st_size, app_png.stat().st_size, app.stat().st_size, flow.stat().st_size, proof.stat().st_size)" }
    Invoke-Native "proof manifest" { python .\scripts\verify-proof-manifest.py }
    Invoke-Native "proof schema" { python -c "import proof_report; payload=proof_report.build_payload(); proof=payload['local_proof']; gate=proof['package_build_gate']; meta=proof['package_metadata']; actions=payload['next_actions']; first=actions[0]['command'].replace(chr(92), '/') if actions else ''; commands=[x['command'].replace(chr(92), '/') for x in actions]; blockers=' | '.join(payload['public_blockers']); assert gate['status'] in ('command-gated','missing'), gate; assert gate['command']=='scripts/release-check.ps1', gate; assert meta['status']=='ok' and 'repair' in meta['keywords'] and 'Repository' in meta['urls'], meta; assert proof['release_package']['status'] in ('ok','blocked','stale'), proof['release_package']; assert actions and first=='./scripts/release-packet.ps1' and './scripts/post-publish-audit.ps1 -Json' in commands and all(not x['changes_remote'] for x in actions), actions; assert 'KEYSURGEON_POST_PUBLISH_READY' in blockers and 'final v0.2.0 release' in blockers, blockers; print('PROOF_SCHEMA_OK', gate['status'], meta['status'], proof['release_package']['status'], len(actions))" }
    Invoke-Native "app demo current panels" { python -c "from pathlib import Path; import html; raw=Path('site/assets/keysurgeon-app.svg').read_text(encoding='utf-8'); svg=html.unescape(raw).replace('\xa0',' ').replace(chr(92), '/'); proof=Path('site/assets/keysurgeon-proof.json').read_text(encoding='utf-8'); required=('READINESS','REPAIR LADDER','ACTION BAR','ISSUE PACKET','CLI FLOW','DEVICE','repair model:','COMMAND CENTER','FORENSIC SIGNAL RAIL','metadata:','next:','ready: keysurgeon ready','keysurgeon ready','./scripts/release-packet.ps1','post-publish-audit.ps1','KEYSURGEON_POST_PUBLISH_READY','final','v0.2.0 release'); missing=[x for x in required if x not in svg]; assert not missing, missing; assert 'readiness, repair ladder, action bar, issue packet' in proof; print('APP_DEMO_PANELS_OK', len(required))" }
    Invoke-Native "textual app runtime smoke" { python .\scripts\verify-textual-app.py }
    Invoke-Native "landing metadata" { python .\scripts\verify-landing-metadata.py }
    Invoke-Native "landing copy sentinels" { python -c "from pathlib import Path; html=Path('site/index.html').read_text(encoding='utf-8'); css=Path('site/assets/keysurgeon.css').read_text(encoding='utf-8'); readme=Path('README.md').read_text(encoding='utf-8'); workflow=Path('.github/workflows/pages.yml').read_text(encoding='utf-8'); meta=Path('docs/GITHUB_METADATA.md').read_text(encoding='utf-8'); launch=Path('docs/LAUNCH_PACKET.md').read_text(encoding='utf-8'); checklist=Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8'); notes=Path('docs/RELEASE_NOTES_0.2.0.md').read_text(encoding='utf-8'); required=('See install steps','Windows','MIT','local JSON','Rich + Textual','See the signal','--plain fallback','Sample diagnosis copy','keysurgeon ready','keysurgeon proof --json','assets/keysurgeon-flow.svg','workflow, Rich, and Textual proof','Install from the checkout today','python -m pip install .','post-publish path'); html_only=('View on GitHub','https://github.com/nosafune/keysurgeon','Compare it to a browser keyboard tester.','KEYBOARD_TESTER_COMPARISON.md'); missing_html=[x for x in required + html_only if x not in html]; missing_workflow=[x for x in required if x not in workflow]; assert not missing_html, missing_html; assert not missing_workflow, missing_workflow; assert '.button.ghost' in css and '.text-link' in css; assert '## Contributing' in readme and 'CONTRIBUTING.md' in readme and 'docs/FIRST_ISSUES.md' in readme and 'docs/STARTER_ISSUE_TEMPLATES.md' in readme; assert 'keyboard-tester' in meta; launch_required=('headless landing screenshots','proof manifest','Windows Terminal','rasterized captures','keysurgeon ready'); missing_launch=[x for x in launch_required if x not in launch]; assert not missing_launch, missing_launch; assert 'keysurgeon.py ready' in checklist; assert 'browser-rasterized Rich/Textual demo PNGs plus workflow and source SVG generation' in notes; print('LANDING_COPY_SENTINELS_OK', len(required) + len(html_only))" }
    Invoke-Native "landing iconography and tabs" { python -c "from pathlib import Path; html=Path('site/index.html').read_text(encoding='utf-8'); css=Path('site/assets/keysurgeon.css').read_text(encoding='utf-8'); required_html=('role=','tablist','tabpanel','aria-controls=','tab-diagnosis','aria-labelledby=','tabbtn-diagnosis','tabindex=','-1','ks-icon-diagnosis','ks-icon-signal','ks-icon-investigator','ks-icon-repair','ks-icon-privacy','ks-icon-install','Home','End'); required_css=('.icon-sprite','.tab-icon','.button-icon','stroke: currentColor'); missing_html=[x for x in required_html if x not in html]; missing_css=[x for x in required_css if x not in css]; assert not missing_html, missing_html; assert not missing_css, missing_css; print('LANDING_ICONOGRAPHY_TABS_OK', len(required_html), len(required_css))" }
    Invoke-Native "site command sentinels" { python -c "from pathlib import Path; cli=Path('keysurgeon.py').read_text(encoding='utf-8'); readme=Path('README.md').read_text(encoding='utf-8'); checklist=Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8'); site=Path('site/index.html').read_text(encoding='utf-8'); required_cli=('keysurgeon site [--open]','mode_site','public URL is not claimed until GitHub Pages passes','keysurgeon tour','mode_tour','keysurgeon ready','mode_ready'); required_readme=('keysurgeon site','keysurgeon site --open','keysurgeon tour','keysurgeon ready','concise local launch readiness board'); required_checklist=('keysurgeon-flow.svg','keysurgeon-proof.json'); assert all(x in cli for x in required_cli), required_cli; assert all(x in readme for x in required_readme), required_readme; assert all(x in checklist for x in required_checklist), required_checklist; assert 'keysurgeon tour' in site; print('SITE_COMMAND_SENTINELS_OK', len(required_cli) + len(required_readme) + len(required_checklist) + 1)" }
    Invoke-Native "support proof sentinels" { python -c "from pathlib import Path; paths=[Path('.github/ISSUE_TEMPLATE/bug_report.yml'), Path('.github/ISSUE_TEMPLATE/board_report.yml'), Path('.github/ISSUE_TEMPLATE/manual_smoke_report.yml'), Path('SUPPORT.md'), Path('docs/DIAGNOSIS_GUIDE.md')]; missing=[str(p) for p in paths if 'keysurgeon proof --json' not in p.read_text(encoding='utf-8')]; assert not missing, missing; bug=Path('.github/ISSUE_TEMPLATE/bug_report.yml').read_text(encoding='utf-8'); support=Path('SUPPORT.md').read_text(encoding='utf-8'); cli=Path('keysurgeon.py').read_text(encoding='utf-8'); issue=Path('issue_packet.py').read_text(encoding='utf-8'); assert 'keysurgeon issue --out' in bug and 'keysurgeon issue --out' in support and 'keysurgeon issue' in cli and 'KeySurgeon Issue Packet' in issue and 'Do not paste typed private text' in issue; print('SUPPORT_PROOF_SENTINELS_OK', len(paths))" }
    Invoke-Native "manual smoke issue template" { python -c "from pathlib import Path; import re, yaml; script=Path('scripts/record-manual-smoke-result.ps1').read_text(encoding='utf-8'); template=yaml.safe_load(Path('.github/ISSUE_TEMPLATE/manual_smoke_report.yml').read_text(encoding='utf-8')); expected=re.search(r'ValidateSet\(([^)]*)\)', script).group(1); expected=[x.strip().strip(chr(34)) for x in expected.split(',')]; result=[field for field in template['body'] if field.get('id')=='result'][0]; options=result['attributes']['options']; assert options == expected, (options, expected); text=Path('.github/ISSUE_TEMPLATE/manual_smoke_report.yml').read_text(encoding='utf-8'); docs=Path('docs/MANUAL_KEYBOARD_SMOKE.md').read_text(encoding='utf-8') + Path('README.md').read_text(encoding='utf-8') + Path('docs/DIAGNOSIS_GUIDE.md').read_text(encoding='utf-8'); docs_norm=docs.replace(chr(92), '/'); cli=Path('keysurgeon.py').read_text(encoding='utf-8'); manual=Path('manual_smoke.py').read_text(encoding='utf-8'); assert 'docs/MANUAL_SMOKE_REPORT.md' in text and 'keysurgeon export --json' in text and 'typed private text' in text; assert 'keysurgeon smoke' in cli and 'keysurgeon smoke --check FILE' in cli and 'keysurgeon smoke --out' in docs and 'keysurgeon smoke --check docs/MANUAL_SMOKE_REPORT.md' in docs_norm and 'validation_errors' in manual and 'does not prove hardware behavior' in manual; print('MANUAL_SMOKE_TEMPLATE_OK', len(options))" }
    Invoke-Native "manual smoke recorder hardening" { python -c "from pathlib import Path; recorder=Path('scripts/record-manual-smoke-result.ps1').read_text(encoding='utf-8'); test=Path('scripts/test-manual-smoke-gate.ps1').read_text(encoding='utf-8'); docs=Path('docs/MANUAL_KEYBOARD_SMOKE.md').read_text(encoding='utf-8') + Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8') + Path('docs/PUBLISH_RUNBOOK.md').read_text(encoding='utf-8') + Path('CHANGELOG.md').read_text(encoding='utf-8') + Path('docs/RELEASE_NOTES_0.2.0.md').read_text(encoding='utf-8'); docs_norm=docs.replace(chr(92), '/'); proof=Path('proof_report.py').read_text(encoding='utf-8'); required=('Assert-CompletedEvidenceReport','blank Pass/Fail and Evidence table cells','install-source placeholder','keyboard brand/model','hardware-smoke-pass'); missing=[x for x in required if x not in recorder]; assert not missing, missing; assert 'Recorder accepted an incomplete manual smoke scaffold' in test and 'complete-report.md' in test; assert 'blank scaffolds' in docs and 'install-source placeholder' in docs and 'filled result' in docs and 'table cells' in docs and 'keysurgeon smoke --check docs/MANUAL_SMOKE_REPORT.md' in docs_norm and 'keysurgeon smoke --check' in proof; print('MANUAL_SMOKE_RECORDER_HARDENING_OK', len(required))" }
    Invoke-Native "github label docs" { python -c "from pathlib import Path; import yaml; q=chr(34); issue_labels=set(); [issue_labels.update(yaml.safe_load(p.read_text(encoding='utf-8')).get('labels', [])) for p in Path('.github/ISSUE_TEMPLATE').glob('*.yml') if p.name != 'config.yml']; expected_issue={'bug','board-data','enhancement','hardware-smoke'}; setup=Path('scripts/github-setup-plan.ps1').read_text(encoding='utf-8'); doc=Path('docs/GITHUB_LABELS.md').read_text(encoding='utf-8'); all_labels=expected_issue | {'good first issue','help wanted'}; missing=[label for label in sorted(all_labels) if f'`{label}`' not in doc or f'Name = {q}{label}{q}' not in setup]; assert issue_labels == expected_issue, issue_labels; assert not missing, missing; assert 'unsupported scope' in doc and 'docs/GITHUB_LABELS.md' in Path('docs/PUBLISH_RUNBOOK.md').read_text(encoding='utf-8') and 'docs/GITHUB_LABELS.md' in Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8'); assert 'good first issue' in Path('docs/PUBLISH_RUNBOOK.md').read_text(encoding='utf-8') and 'help wanted' in Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8'); print('GITHUB_LABEL_DOCS_OK', len(all_labels))" }
    Invoke-Native "first issues docs" { python -c "from pathlib import Path; doc=Path('docs/FIRST_ISSUES.md').read_text(encoding='utf-8'); templates=Path('docs/STARTER_ISSUE_TEMPLATES.md').read_text(encoding='utf-8'); readme=Path('README.md').read_text(encoding='utf-8'); contrib=Path('CONTRIBUTING.md').read_text(encoding='utf-8'); launch=Path('docs/LAUNCH_PACKET.md').read_text(encoding='utf-8'); meta=Path('docs/GITHUB_METADATA.md').read_text(encoding='utf-8'); checklist=Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8'); runbook=Path('docs/PUBLISH_RUNBOOK.md').read_text(encoding='utf-8'); seed=Path('scripts/seed-starter-issues-plan.ps1').read_text(encoding='utf-8'); required=('Board Data','Repair Ladder Wording','Install Friction','Test Coverage','Not Starter Scope','keysurgeon export --json','python keysurgeon.py selftest','verify-public-tree.ps1','No typed private text','real keyboard smoke pass','good first issue','help wanted'); missing=[x for x in required if x not in doc]; assert not missing, missing; template_required=('Board Data','Install Friction','Repair Ladder Wording','Test Coverage','Manual Hardware Smoke Evidence','hardware-smoke-pass','Do not infer hot-swap support from USB vendor ID alone','No real typed text is added','Do not add typed private text','Claims that GitHub Actions, Pages, releases, or executable downloads exist','good first issue','help wanted','seed-starter-issues-plan.ps1','gh issue create'); missing_templates=[x for x in template_required if x not in templates]; assert not missing_templates, missing_templates; refs=[readme, contrib, launch, meta, checklist, runbook, doc, templates]; assert all('docs/STARTER_ISSUE_TEMPLATES.md' in x for x in refs[:-1]), 'starter template reference missing'; assert all('seed-starter-issues-plan.ps1' in x for x in (launch, meta, checklist, runbook, templates)); assert 'docs/FIRST_ISSUES.md' in readme and 'docs/FIRST_ISSUES.md' in contrib; assert 'good first issue' in meta and 'help wanted' in checklist; assert 'KEYSURGEON_STARTER_ISSUES_PLAN_OK' in seed and 'gh issue create' in seed and 'dry-run only' in seed; print('FIRST_ISSUES_DOCS_OK', len(required), len(template_required))" }
    Invoke-Native "proof matrix docs" { python -c "from pathlib import Path; doc=Path('docs/PROOF_MATRIX.md').read_text(encoding='utf-8'); readme=Path('README.md').read_text(encoding='utf-8'); launch=Path('docs/LAUNCH_PACKET.md').read_text(encoding='utf-8'); metadata=Path('docs/GITHUB_METADATA.md').read_text(encoding='utf-8'); notes=Path('docs/RELEASE_NOTES_0.2.0.md').read_text(encoding='utf-8'); checklist=Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8'); comparison=Path('docs/KEYBOARD_TESTER_COMPARISON.md').read_text(encoding='utf-8'); required=('Rich terminal output is wired','Textual command center is wired','Landing page has real local screenshots','Package metadata matches search positioning','Package build path works','Export avoids typed private text','Release files are committed','Broad real-keyboard hardware behavior','Public GitHub repository exists','Remote selftest is green','GitHub Pages homepage exists','GitHub release asset exists','GitHub visibility is complete','KEYSURGEON_POST_PUBLISH_READY','post-publish-audit.ps1 -Json','published-visible','local-ready','command-gated','blocked','verify-textual-app.py','headless Textual'); missing=[x for x in required if x not in doc]; assert not missing, missing; refs=[('docs/PROOF_MATRIX.md' in readme),('docs/PROOF_MATRIX.md' in launch),('Proof matrix' in metadata),('proof-matrix' in notes),('verify-textual-app.py' in launch),('KEYSURGEON_TEXTUAL_APP_SMOKE_OK' in checklist),('headless Textual mount/action smoke' in comparison),('headless Textual app smoke' in notes)]; assert all(refs), refs; print('PROOF_MATRIX_DOCS_OK', len(required))" }
    Invoke-Native "keyboard tester comparison" { python -c "from pathlib import Path; readme=Path('README.md').read_text(encoding='utf-8'); comp=Path('docs/KEYBOARD_TESTER_COMPARISON.md').read_text(encoding='utf-8'); required=('Keyboard Tester Vs KeySurgeon','double-fires','keysurgeon watch','keysurgeon export --json','keysurgeon proof --json','hardware-smoke-pass'); missing=[x for x in required if x not in comp]; assert not missing, missing; assert 'docs/KEYBOARD_TESTER_COMPARISON.md' in readme; print('KEYBOARD_TESTER_COMPARISON_OK', len(required))" }
    Invoke-Native "readme badges" { python -c "from pathlib import Path; readme=Path('README.md').read_text(encoding='utf-8'); required=('Python 3.10+','Windows','License: MIT','Rich UI','Textual app','Local JSON','No telemetry'); missing=[x for x in required if x not in readme]; forbidden=('github/actions/workflow/status','pypi/v','release-latest'); bad=[x for x in forbidden if x in readme.lower()]; assert not missing, missing; assert not bad, bad; print('README_BADGES_OK', len(required))" }
    Invoke-Native "readme install order" { python -c "from pathlib import Path; text=Path('README.md').read_text(encoding='utf-8'); local='Current local install, from this checkout'; remote='Future public GitHub install, after the repository is created, pushed, and the'; guard='Do not use the GitHub URL yet unless'; assert local in text and remote in text and guard in text, (local in text, remote in text, guard in text); assert text.index(local) < text.index(remote) < text.index(guard); assert 'python -m pip install .' in text and 'git+https://github.com/nosafune/keysurgeon.git' in text; print('README_INSTALL_ORDER_OK')" }
    Invoke-Native "readme first five minutes" { python -c "from pathlib import Path; readme=Path('README.md').read_text(encoding='utf-8'); launch=Path('docs/LAUNCH_PACKET.md').read_text(encoding='utf-8'); required=('First Five Minutes','keysurgeon tour','keysurgeon test E','keysurgeon fix E','keysurgeon ready','keysurgeon proof --json','keysurgeon watch --bg','keysurgeon issue','without typed private text'); missing=[x for x in required if x not in readme]; assert not missing, missing; assert readme.index('First Five Minutes') < readme.index('Why Not A Keyboard Tester?'); launch_required=('First-Run Copy','Try the local loop','replace only as the last rung'); missing_launch=[x for x in launch_required if x not in launch]; assert not missing_launch, missing_launch; print('README_FIRST_FIVE_MINUTES_OK', len(required), len(launch_required))" }
    Invoke-Native "readme publish status" { python -c "from pathlib import Path; text=Path('README.md').read_text(encoding='utf-8'); required=('What You Get In 30 Seconds','browser keyboard tester says a key works','Current Publish Status','public-ready locally, not published','v2 release files must be committed','hardware-smoke-pass','GitHub repository and origin remote do not exist yet','remote selftest and Pages workflow runs do not exist yet','launch-readiness.ps1','one-page local launch board','without touching git, GitHub, releases, Pages, or deploy state','keysurgeon proof --json','pre-publish-audit.ps1'); missing=[x for x in required if x not in text]; assert not missing, missing; assert text.index('What You Get In 30 Seconds') < text.index('Current Publish Status'); print('README_PUBLISH_STATUS_OK', len(required))" }
    Invoke-Native "readme linked media" { python -c "from pathlib import Path; text=Path('README.md').read_text(encoding='utf-8'); assert text.count('[![') >= 13; assert 'site/assets/keysurgeon-landing-desktop.png' in text; assert 'site/assets/keysurgeon-flow.svg' in text; assert 'site/assets/keysurgeon-demo.png' in text; assert 'site/assets/keysurgeon-app.png' in text; assert '](' + 'site/index.html' + ')' in text; assert '](' + 'docs/DIAGNOSIS_GUIDE.md' + ')' in text; print('README_LINKED_MEDIA_OK', text.count('[!['))" }
    Invoke-Native "readme first fold motion" { python -c "from pathlib import Path; text=Path('README.md').read_text(encoding='utf-8'); flow='site/assets/keysurgeon-flow.svg'; desktop='site/assets/keysurgeon-landing-desktop.png'; required=('Animated SVG demo of the local command loop','without claiming hardware or','remote publish proof','animated workflow strip is an SVG generated from seeded command frames'); missing=[x for x in required if x not in text]; assert not missing, missing; assert text.index(flow) < text.index(desktop); print('README_FIRST_FOLD_MOTION_OK', len(required))" }
    Invoke-Native "release notes changelog parity" { python -c "from pathlib import Path; changelog=Path('CHANGELOG.md').read_text(encoding='utf-8'); notes=Path('docs/RELEASE_NOTES_0.2.0.md').read_text(encoding='utf-8'); notes_l=notes.lower(); required=('launch-readiness','no-mutation launch-readiness board','hardened manual smoke','blank scaffold','hardware-smoke-pass'); missing_changelog=[x for x in ('launch-readiness.ps1','hardware-smoke-pass','blank','evidence','scaffolds') if x not in changelog]; missing_notes=[x for x in required if x not in notes_l]; assert not missing_changelog, missing_changelog; assert not missing_notes, missing_notes; print('RELEASE_NOTES_CHANGELOG_PARITY_OK', len(required))" }
    Invoke-Native "release manifest sentinels" { python -c "from pathlib import Path; script=Path('scripts/package-release-asset.ps1').read_text(encoding='utf-8'); build=Path('scripts/build-exe.ps1').read_text(encoding='utf-8'); docs=Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8') + Path('docs/PUBLISH_RUNBOOK.md').read_text(encoding='utf-8'); required=('public_demo_proof','proof_snapshot','KEYSURGEON_RELEASE_PROOF_SHA256','package_build_gate','command-gated package build'); missing=[x for x in required if x not in script or x not in docs]; assert not missing, missing; build_required=('pyproject.toml;.','scripts\\release-check.ps1;scripts'); missing_build=[x for x in build_required if x not in build]; assert not missing_build, missing_build; print('RELEASE_MANIFEST_SENTINELS_OK', len(required), len(build_required))" }
    Invoke-Native "local release proof gate sentinels" { python -c "from pathlib import Path; script=Path('scripts/local-release-proof.ps1').read_text(encoding='utf-8'); docs=Path('docs/PUBLISH_RUNBOOK.md').read_text(encoding='utf-8') + Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8') + Path('README.md').read_text(encoding='utf-8'); required=('release files committed','latest release','GitHub release asset','KEYSURGEON_REMOTE_GATES_BLOCKED_EXPECTED','post-publish-audit.ps1','KEYSURGEON_POST_PUBLISH_BLOCKED','KEYSURGEON_POST_PUBLISH_GATES_BLOCKED_EXPECTED','GitHub Pages URL','starter issues'); missing=[x for x in required if x not in script]; assert not missing, missing; docs_required=('KEYSURGEON_POST_PUBLISH_GATES_BLOCKED_EXPECTED','post-publish visibility audit','final release'); missing_docs=[x for x in docs_required if x not in docs]; assert not missing_docs, missing_docs; print('LOCAL_RELEASE_PROOF_GATE_SENTINELS_OK', len(required), len(docs_required))" }
    Invoke-Native "release warning gate" { python -c "from pathlib import Path; script=Path('scripts/release-check.ps1').read_text(encoding='utf-8'); required=('WHEEL_LICENSE_WARNINGS_CLEAN','SetuptoolsDeprecationWarning','Package metadata emitted deprecated license warnings','Package metadata emitted an unexpected SetuptoolsDeprecationWarning','RedirectStandardOutput','RedirectStandardError','keysurgeon-wheel-','Remove-Item -LiteralPath'); missing=[x for x in required if x not in script]; assert not missing, missing; print('RELEASE_WARNING_GATE_OK', len(required))" }
    Invoke-Native "hidden process gates" { python -c "from pathlib import Path; files=['scripts/export-social-preview.ps1','scripts/export-landing-screenshots.ps1','scripts/export-terminal-screenshots.ps1','scripts/verify-site-render.ps1','scripts/release-check.ps1','scripts/verify-public-tree.ps1']; browser_files=files[:4]; required_flags=('--headless=new','--disable-first-run-ui','--no-first-run','--no-default-browser-check','--user-data-dir='); cleanup='Remove-Item -LiteralPath '+chr(36)+'profilePath -Recurse -Force'; missing_hidden=[path for path in files if '-WindowStyle Hidden' not in Path(path).read_text(encoding='utf-8')]; missing_flags=[(path, flag) for path in browser_files for flag in required_flags if flag not in Path(path).read_text(encoding='utf-8')]; missing_cleanup=[path for path in browser_files if 'keysurgeon-browser-profile-' not in Path(path).read_text(encoding='utf-8') or cleanup not in Path(path).read_text(encoding='utf-8')]; assert not missing_hidden, missing_hidden; assert not missing_flags, missing_flags; assert not missing_cleanup, missing_cleanup; assert all('Invoke-HiddenBrowser' in Path(path).read_text(encoding='utf-8') for path in browser_files); print('HIDDEN_PROCESS_GATES_OK', len(files), len(required_flags))" }
    Invoke-Native "pre-publish release asset gate" {
        $check = @'
from pathlib import Path
script = Path('scripts/pre-publish-audit.ps1').read_text(encoding='utf-8')
proof = Path('scripts/local-release-proof.ps1').read_text(encoding='utf-8')
docs = (
    Path('README.md').read_text(encoding='utf-8')
    + Path('docs/PUBLISH_RUNBOOK.md').read_text(encoding='utf-8')
    + Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8')
)
required = (
    'gh release view',
    'GitHub release asset',
    'no GitHub release asset visible',
    'release files committed',
    'git status --porcelain -- .',
    '[switch]$Json',
    'ConvertTo-Json',
    'status =',
    'blocked',
    'ready',
)
missing = [x for x in required if x not in script]
assert not missing, missing
assert 'release files committed' in proof
assert 'pre-publish-audit.ps1 -Json' in docs
print('PRE_PUBLISH_RELEASE_ASSET_GATE_OK', len(required))
'@
        python -c $check
    }
    Invoke-Native "post-publish visibility gate" {
        $check = @'
from pathlib import Path
script = Path('scripts/post-publish-audit.ps1').read_text(encoding='utf-8')
docs = (
    Path('README.md').read_text(encoding='utf-8')
    + Path('docs/PUBLISH_RUNBOOK.md').read_text(encoding='utf-8')
    + Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8')
    + Path('docs/GITHUB_METADATA.md').read_text(encoding='utf-8')
    + Path('docs/LAUNCH_PACKET.md').read_text(encoding='utf-8')
    + Path('docs/RELEASE_NOTES_0.2.0.md').read_text(encoding='utf-8')
)
packet = Path('scripts/release-packet.ps1').read_text(encoding='utf-8')
required_script = (
    'KEYSURGEON_POST_PUBLISH_READY',
    'KEYSURGEON_POST_PUBLISH_BLOCKED',
    'gh repo view',
    'gh label list',
    'gh issue list',
    'gh run list',
    'gh api "repos/$Repo/pages"',
    'gh release view',
    'repositoryTopics',
    'v0.2.0',
    'isPrerelease',
    'keysurgeon-v0.2.0-windows-x64.exe',
    'ConvertTo-Json',
)
missing_script = [x for x in required_script if x not in script]
assert not missing_script, missing_script
required_docs = (
    'post-publish-audit.ps1',
    'KEYSURGEON_POST_PUBLISH_READY',
    'starter issues',
    'Pages URL',
    'release asset',
)
missing_docs = [x for x in required_docs if x not in docs]
assert not missing_docs, missing_docs
assert 'post-publish-audit.json' in packet and 'files: 10' in packet
print('POST_PUBLISH_VISIBILITY_GATE_OK', len(required_script), len(required_docs))
'@
        python -c $check
    }
    Invoke-Native "release commit plan sentinels" { python -c "from pathlib import Path; script=Path('scripts/release-commit-plan.ps1').read_text(encoding='utf-8'); audit=Path('scripts/pre-publish-audit.ps1').read_text(encoding='utf-8'); docs=Path('docs/PUBLISH_RUNBOOK.md').read_text(encoding='utf-8') + Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8'); required=('KEYSURGEON_RELEASE_COMMIT_PLAN','dry-run only','no git add or git commit is executed','git_root:','project_root:','git -C {0} add --','git -C {0} commit -m','blocked_artifacts','clean-artifacts.ps1','Prepare KeySurgeon v0.2.0 public release','distribution_mirror:','distribution_mirror_scope:','verify-dist-parity.ps1'); missing=[x for x in required if x not in script]; assert not missing, missing; assert 'release-commit-plan.ps1' in audit and 'release-commit-plan.ps1' in docs and 'distribution mirror has parity' in docs; print('RELEASE_COMMIT_PLAN_SENTINELS_OK', len(required))" }
    Invoke-Native "release packet sentinels" { python -c "from pathlib import Path; script=Path('scripts/release-packet.ps1').read_text(encoding='utf-8'); docs=Path('docs/PUBLISH_RUNBOOK.md').read_text(encoding='utf-8') + Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8') + Path('docs/LAUNCH_PACKET.md').read_text(encoding='utf-8'); gitignore=Path('.gitignore').read_text(encoding='utf-8'); clean=Path('scripts/clean-artifacts.ps1').read_text(encoding='utf-8'); commit=Path('scripts/release-commit-plan.ps1').read_text(encoding='utf-8'); required=('KEYSURGEON_RELEASE_PACKET_OK','pre-publish-audit.ps1','post-publish-audit.ps1','post-publish-audit.json','release-commit-plan.ps1','github-setup-plan.ps1','seed-starter-issues-plan.ps1','starter-issues-plan.md','launch-readiness.ps1','launch-readiness.md','keysurgeon.py proof --json','public-asset-proof.json','launch-copy.md','local dry-run only','files: 10'); missing=[x for x in required if x not in script]; assert not missing, missing; assert 'release-packet.ps1' in docs and 'seed-starter-issues-plan.ps1' in docs and 'launch-readiness.ps1' in docs and 'post-publish-audit.ps1' in docs and 'artifacts/' in gitignore and 'artifacts' in clean and 'artifacts/' in commit; print('RELEASE_PACKET_SENTINELS_OK', len(required))" }
    Invoke-Native "dist parity sentinels" { python -c "from pathlib import Path; script=Path('scripts/verify-dist-parity.ps1').read_text(encoding='utf-8'); docs=Path('docs/PUBLISH_RUNBOOK.md').read_text(encoding='utf-8') + Path('docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8'); required=('KEYSURGEON_DIST_PARITY_OK','KEYSURGEON_DIST_PARITY_FAIL','DistRoot','Get-FileHash','artifacts','__pycache__','keysurgeon_profile\\.json','keysurgeon_boards\\.json'); missing=[x for x in required if x not in script]; assert not missing, missing; assert 'verify-dist-parity.ps1' in docs and 'public handoff tree' in docs; print('DIST_PARITY_SENTINELS_OK', len(required))" }
    Invoke-Native "launch readiness board" {
        $testDir = Join-Path $PWD ".runtime\launch-readiness-test"
        New-Item -ItemType Directory -Force -Path $testDir | Out-Null
        $auditPath = Join-Path $testDir "audit.json"
        $proofPath = Join-Path $testDir "proof.json"
        @'
{
  "tool": "KeySurgeon",
  "status": "blocked",
  "repo": "nosafune/keysurgeon",
  "checks": [
    { "status": "ok", "name": "local public tree", "detail": "KEYSURGEON_PUBLIC_TREE_OK" },
    { "status": "missing", "name": "manual keyboard smoke", "detail": "docs/MANUAL_SMOKE_RESULT.md missing" },
    { "status": "missing", "name": "git remote origin", "detail": "no origin configured" }
  ],
  "failures": [
    "manual keyboard smoke: docs/MANUAL_SMOKE_RESULT.md missing",
    "git remote origin: no origin configured"
  ]
}
'@ | Set-Content -LiteralPath $auditPath -Encoding utf8
        $postAuditPath = Join-Path $testDir "post-publish-audit.json"
        @'
{
  "tool": "KeySurgeon",
  "status": "blocked",
  "repo": "nosafune/keysurgeon",
  "checks": [
    { "status": "missing", "name": "GitHub repository", "detail": "gh could not view nosafune/keysurgeon" },
    { "status": "missing", "name": "GitHub release asset", "detail": "no GitHub release visible" }
  ],
  "failures": [
    "GitHub repository: gh could not view nosafune/keysurgeon",
    "GitHub release asset: no GitHub release visible"
  ]
}
'@ | Set-Content -LiteralPath $postAuditPath -Encoding utf8
        @'
{
  "tool": "KeySurgeon",
  "proof_summary": {
    "local": 8,
    "command_gated": 1,
    "blocked": 6
  }
}
'@ | Set-Content -LiteralPath $proofPath -Encoding utf8
        $board = & powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\launch-readiness.ps1 -Repo nosafune/keysurgeon -AuditPath $auditPath -PostPublishAuditPath $postAuditPath -ProofPath $proofPath
        if ($LASTEXITCODE -ne 0) {
            throw "launch-readiness.ps1 failed with exit code $LASTEXITCODE."
        }
        $text = $board -join "`n"
        $required = @(
            "KEYSURGEON_LAUNCH_READINESS",
            "mode: local summary only; no git, GitHub, release, Pages, or deploy changes are made",
            "local_proof: 8 local / 1 command-gated / 6 blocked",
            "post_publish_status: blocked",
            "post_publish_gates: 0 ok / 2 missing",
            "post-publish gate board:",
            "manual keyboard smoke",
            "git remote origin",
            "GitHub release asset",
            "KEYSURGEON_LAUNCH_READINESS_OK"
        )
        $missing = @($required | Where-Object { -not $text.Contains($_) })
        if ($missing.Count) {
            throw "Missing launch readiness sentinels: $($missing -join ', ')"
        }
        Write-Host "LAUNCH_READINESS_BOARD_OK"
    }
    Invoke-Native "starter issue seed plan" {
        $starterPlan = & powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\seed-starter-issues-plan.ps1 -Repo nosafune/keysurgeon
        if ($LASTEXITCODE -ne 0) {
            throw "starter issue seed plan command failed with exit code $LASTEXITCODE."
        }
        $starterText = $starterPlan -join "`n"
        $starterRequired = @(
            "KEYSURGEON_STARTER_ISSUES_PLAN",
            "mode: dry-run only; no gh commands are executed",
            'gh issue create --repo nosafune/keysurgeon --title "[board-data]: add conservative repair hint for a known board"',
            'gh issue create --repo nosafune/keysurgeon --title "[docs]: clarify Windows install friction before first selftest"',
            'gh issue create --repo nosafune/keysurgeon --title "[docs]: make one repair ladder phrase clearer"',
            'gh issue create --repo nosafune/keysurgeon --title "[test]: cover one fault, export, proof, or UI state"',
            'gh issue create --repo nosafune/keysurgeon --title "[hardware-smoke]: record real keyboard smoke for one install path"',
            'KEYSURGEON_STARTER_ISSUES_PLAN_OK 5 issues'
        )
        $missingStarter = @($starterRequired | Where-Object { -not $starterText.Contains($_) })
        if ($missingStarter.Count) {
            throw "Missing starter issue plan sentinels: $($missingStarter -join ', ')"
        }
        Write-Host "STARTER_ISSUE_SEED_PLAN_OK"
    }
    Invoke-Native "github setup plan" {
        $setupPlan = & powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\github-setup-plan.ps1 -Repo nosafune/keysurgeon
        if ($LASTEXITCODE -ne 0) {
            throw "github setup plan command failed with exit code $LASTEXITCODE."
        }
        $setupText = $setupPlan -join "`n"
        $setupRequired = @(
            "KEYSURGEON_GITHUB_SETUP_PLAN",
            "mode: dry-run only; no gh commands are executed",
            "gh repo create nosafune/keysurgeon --public",
            "--disable-wiki --clone=false",
            "gh repo edit nosafune/keysurgeon --description",
            "--add-topic keyboard,keyboard-tester,keyboard-diagnostics,keyboard-chatter,keyboard-repair,double-typing,dead-keys,debounce,mechanical-keyboard,usb-hid,hardware-diagnostics,windows,cli,rich,textual,repair",
            'gh label create "hardware-smoke"',
            'gh label create "good first issue"',
            'gh label create "help wanted"',
            "use the create command only if keysurgeon does not already exist",
            "KEYSURGEON_GITHUB_SETUP_PLAN_OK 16 topics 6 labels"
        )
        $missingSetup = @($setupRequired | Where-Object { $setupText -notlike "*$_*" })
        if ($missingSetup.Count) {
            throw "Missing github setup plan sentinels: $($missingSetup -join ', ')"
        }
        Write-Host "GITHUB_SETUP_PLAN_OK"
    }
    $psErrors = @()
    foreach ($script in Get-ChildItem -LiteralPath "scripts" -Filter "*.ps1" -File) {
        $null = [System.Management.Automation.PSParser]::Tokenize(
            (Get-Content -LiteralPath $script.FullName -Raw),
            [ref]$psErrors
        )
    }
    if ($psErrors.Count) {
        $psErrors | Format-List *
        throw "PowerShell script parse failed."
    }
    Write-Host "POWERSHELL_PARSE_OK"
    $scriptPyFiles = Get-ChildItem -LiteralPath "scripts" -Filter "*.py" -File | ForEach-Object { $_.FullName }
    if ($scriptPyFiles) {
        foreach ($scriptPy in $scriptPyFiles) {
            Invoke-Native "compile script $scriptPy" { python -m py_compile $scriptPy }
        }
        Write-Host "SCRIPT_PY_COMPILE_OK"
    }
    Invoke-Native "workflow python support sentinels" {
        $selftestWorkflow = Get-Content -LiteralPath ".github\workflows\selftest.yml" -Raw
        $exeWorkflow = Get-Content -LiteralPath ".github\workflows\windows-exe.yml" -Raw
        $workflowDocs = (Get-Content -LiteralPath "docs\RELEASE_CHECKLIST.md" -Raw) + (Get-Content -LiteralPath "docs\PUBLISH_RUNBOOK.md" -Raw)
        $requiredWorkflow = @(
            '"3.10", "3.11", "3.12"',
            '${{ matrix.python-version }}',
            'fail-fast: false'
        )
        $missingWorkflow = @($requiredWorkflow | Where-Object { -not $selftestWorkflow.Contains($_) })
        if ($missingWorkflow.Count) {
            throw "Missing workflow Python support sentinel: $($missingWorkflow -join ', ')"
        }
        if (-not $exeWorkflow.Contains('python-version: "3.10"')) {
            throw "Windows executable workflow does not use the minimum supported Python."
        }
        foreach ($needle in @("Python 3.10+", "3.11", "3.12")) {
            if (-not $workflowDocs.Contains($needle)) {
                throw "Missing Python support docs sentinel: $needle"
            }
        }
        Write-Host "WORKFLOW_PYTHON_SUPPORT_OK 4"
    }
    Invoke-Native "package metadata" {
        $pyproject = Get-Content -LiteralPath "pyproject.toml" -Raw
        $required = @(
            "requires-python = "">=3.10""",
            "license = ""MIT""",
            "license-files = [""LICENSE""]",
            "setuptools>=77",
            "double-typing",
            "repair-first",
            "keyboard-tester",
            "keyboard-diagnostics",
            "keyboard-chatter",
            "keyboard-repair",
            "dead-keys",
            "debounce",
            "mechanical-keyboard",
            "usb-hid",
            "hardware-diagnostics",
            "rich",
            "textual",
            "repair",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12"
        )
        $missing = @($required | Where-Object { -not $pyproject.Contains($_) })
        if ($missing.Count) {
            throw "Missing package metadata: $($missing -join ', ')"
        }
        if ($pyproject -match 'License ::') {
            throw "Deprecated license classifier is present."
        }
        Write-Host "PACKAGE_METADATA_OK $($required.Count)"
    }
    & (Join-Path $PSScriptRoot "test-manual-smoke-gate.ps1")

    Invoke-Native "public scrub" { python .\scripts\verify-public-scrub.py }

    Write-Host "KEYSURGEON_PUBLIC_TREE_OK"
}
finally {
    Pop-Location
}
