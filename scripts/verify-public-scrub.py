"""Scrub public files for local paths, private names, and debt markers."""

from pathlib import Path


NEEDLES = (
    "C:\\Users",
    "AIDIR",
    "Joey",
    "Codex",
    "CLAUDE",
    "DESIGN.md",
    "keysurgeon_dist",
    "TODO",
    "FIXME",
)

SKIP_DIRS = {"dist", "build", "__pycache__"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".whl", ".exe"}

ROOT_TARGETS = (
    "README.md",
    "CHANGELOG.md",
    "PRODUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "SUPPORT.md",
    "docs",
    "site",
    ".github",
    "pyproject.toml",
)


def iter_files(target: Path):
    if target.is_file():
        yield target
        return
    for path in target.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield path


def main() -> None:
    targets = [Path(name) for name in ROOT_TARGETS]
    targets.extend(path for path in Path(".").glob("*.py"))
    targets.extend(
        path
        for path in Path("scripts").iterdir()
        if path.is_file()
        and path.name not in {"verify-public-tree.ps1", "verify-public-scrub.py"}
    )

    hits = []
    for target in targets:
        if not target.exists():
            continue
        for path in iter_files(target):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), start=1):
                for needle in NEEDLES:
                    if needle in line:
                        hits.append(f"{path}:{line_no}: {needle}")

    if hits:
        for hit in hits:
            print(hit)
        raise SystemExit("Public scrub found local/private/debt references.")

    print("PUBLIC_SCRUB_OK")


if __name__ == "__main__":
    main()
