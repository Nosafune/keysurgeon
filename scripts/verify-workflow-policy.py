"""Verify GitHub workflow safety settings for public readiness."""

from pathlib import Path

import yaml


WORKFLOWS = {
    "selftest.yml": {
        "permissions": {"contents": "read"},
        "timeout": 20,
    },
    "windows-exe.yml": {
        "permissions": {"contents": "read", "actions": "read"},
        "timeout": 30,
    },
    "pages.yml": {
        "permissions": {"contents": "read", "pages": "write", "id-token": "write"},
        "timeout": 10,
    },
}

WORKFLOW_SENTINELS = {
    "selftest.yml": (
        'python-version: ["3.10", "3.11", "3.12"]',
        "fail-fast: false",
        "python-version: ${{ matrix.python-version }}",
    ),
    "windows-exe.yml": (
        'python-version: "3.10"',
        r".\scripts\package-release-asset.ps1",
        "keysurgeon-v*-windows-x64.exe",
        r".\dist\release\SHA256SUMS.txt",
        r".\dist\release\release-manifest.json",
        "keysurgeon-windows-release-asset",
        "dist/release/*",
    ),
}


def main() -> None:
    root = Path(".github/workflows")
    missing = []

    for name, expected in WORKFLOWS.items():
        path = root / name
        data = yaml.safe_load(path.read_text(encoding="utf-8"))

        actual_permissions = data.get("permissions") or {}
        for key, value in expected["permissions"].items():
            if actual_permissions.get(key) != value:
                missing.append(f"{name}:permissions:{key}")

        jobs = data.get("jobs") or {}
        first_job = next(iter(jobs.values()), {})
        if first_job.get("timeout-minutes") != expected["timeout"]:
            missing.append(f"{name}:timeout-minutes")

        text = path.read_text(encoding="utf-8")
        for sentinel in WORKFLOW_SENTINELS.get(name, ()):
            if sentinel not in text:
                missing.append(f"{name}:sentinel:{sentinel}")

    if missing:
        raise SystemExit(f"workflow policy mismatch: {missing}")

    print("WORKFLOW_POLICY_OK", len(WORKFLOWS))


if __name__ == "__main__":
    main()
