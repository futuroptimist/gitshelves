#!/usr/bin/env python3
"""Rewrite imports to match the refactored package layout."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

MAPPING = {
    "gitshelves.fetch": "gitshelves.core.github",
    "gitshelves.scad": "gitshelves.render.scad",
    "gitshelves.baseplate": "gitshelves.render.baseplate",
}


def _rewrite_text(text: str) -> str:
    updated = text
    for old, new in MAPPING.items():
        updated = updated.replace(old, new)
    return updated


def migrate(paths: list[Path], write: bool) -> int:
    """Return the number of files updated or that require updates."""

    changed = 0
    for path in paths:
        original = path.read_text(encoding="utf-8")
        rewritten = _rewrite_text(original)
        if rewritten == original:
            continue
        changed += 1
        if write:
            path.write_text(rewritten, encoding="utf-8")
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Files to inspect")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Apply updates in-place instead of reporting pending changes",
    )
    args = parser.parse_args(argv)

    missing = [str(path) for path in args.paths if not path.exists()]
    if missing:
        parser.error(f"missing paths: {', '.join(missing)}")

    changed = migrate(args.paths, write=args.write)
    if changed == 0:
        print("No changes required")
        return 0

    if args.write:
        print(f"Updated {changed} file{'s' if changed != 1 else ''}")
    else:
        print(
            f"{changed} file{'s' if changed != 1 else ''} need updates. "
            "Re-run with --write to apply replacements."
        )
    return 0


if __name__ == "__main__":  # pragma: no cover - helper script
    sys.exit(main())
