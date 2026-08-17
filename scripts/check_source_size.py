"""Enforce the QAP hand-written source-size budget."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("src", "tests", "scripts", "tools", "web/src")
SOURCE_SUFFIXES = frozenset({".py", ".ts", ".tsx"})
EXCLUDED_PATH_PREFIXES = (
    "scripts/vendor/",
    "src/vendor/",
    "tests/fixtures/",
    "tests/vendor/",
    "tools/vendor/",
    "web/src/vendor/",
)
EXCLUDED_EXACT_PATHS = frozenset(
    {
        "web/src/api/schema.d.ts",
        "web/src/routeTree.gen.ts",
    }
)


def relative_path(path: Path) -> str:
    """Return a stable repository-relative POSIX path."""

    return path.relative_to(ROOT).as_posix()


def is_excluded(path: Path) -> bool:
    """Return whether a known generated or non-source path is excluded."""

    relative = relative_path(path)
    if relative in EXCLUDED_EXACT_PATHS:
        return True
    return relative.startswith(EXCLUDED_PATH_PREFIXES)


def source_files() -> list[Path]:
    """Find eligible source files in deterministic path order."""

    files: list[Path] = []
    for root_name in SCAN_ROOTS:
        scan_root = ROOT / root_name
        if not scan_root.is_dir():
            continue
        files.extend(
            path
            for path in scan_root.rglob("*")
            if path.is_file()
            and path.suffix in SOURCE_SUFFIXES
            and not is_excluded(path)
        )
    return sorted(files, key=relative_path)


def line_count(path: Path) -> int:
    """Count logical text lines without depending on platform newline style."""

    return len(path.read_text(encoding="utf-8").splitlines())


def main() -> int:
    """Print deterministic review warnings/errors and return a process status."""

    warnings: list[tuple[str, int]] = []
    errors: list[tuple[str, int]] = []
    for path in source_files():
        count = line_count(path)
        relative = relative_path(path)
        if 500 <= count <= 700:
            warnings.append((relative, count))
        elif count > 700:
            errors.append((relative, count))

    for relative, count in warnings:
        print(
            f"source-size warning: {relative} has {count} lines "
            "(500-700; review decomposition before adding responsibility)"
        )
    for relative, count in errors:
        print(
            f"source-size error: {relative} has {count} lines "
            "(over the 700-line hand-written limit)"
        )

    if errors:
        print(f"source-size: failed ({len(errors)} file(s) over limit)")
        return 1
    if warnings:
        print(f"source-size: ok ({len(warnings)} review warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
