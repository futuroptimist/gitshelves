"""Helpers to render bundled OpenSCAD templates into STL files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .scad import scad_to_stl


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = PACKAGE_ROOT / "openscad"
DEFAULT_OUTPUT_ROOT = PACKAGE_ROOT / "stl" / "static"

__all__ = [
    "discover_static_scad_files",
    "render_static_stls",
]


def _is_library_path(path: Path, root: Path) -> bool:
    """Return ``True`` when ``path`` lives inside a ``lib`` directory."""

    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return False
    return "lib" in parts


def discover_static_scad_files(root: Path | None = None) -> list[Path]:
    """Return deterministic list of SCAD files under ``root``.

    Directories named ``lib`` are ignored so vendored dependencies are not
    traversed when mirroring the CI build matrix.
    """

    root_path = DEFAULT_SOURCE_ROOT if root is None else Path(root)
    if not root_path.exists():
        return []

    scads: list[Path] = []
    for path in sorted(root_path.rglob("*.scad")):
        if _is_library_path(path, root_path):
            continue
        scads.append(path)
    return scads


def render_static_stls(
    *,
    output_root: Path | None = None,
    source_root: Path | None = None,
) -> list[tuple[Path, Path]]:
    """Render SCAD files under ``source_root`` into STL files.

    Returns a list of ``(scad_path, stl_path)`` pairs for the rendered files.
    """

    src_root = DEFAULT_SOURCE_ROOT if source_root is None else Path(source_root)
    out_root = DEFAULT_OUTPUT_ROOT if output_root is None else Path(output_root)
    rendered: list[tuple[Path, Path]] = []

    for scad_path in discover_static_scad_files(src_root):
        relative = scad_path.relative_to(src_root)
        stl_path = out_root / relative.with_suffix(".stl")
        stl_path.parent.mkdir(parents=True, exist_ok=True)
        scad_to_stl(scad_path.as_posix(), stl_path.as_posix())
        rendered.append((scad_path, stl_path))

    return rendered


def _cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render bundled OpenSCAD templates into STL files",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Directory containing SCAD templates (defaults to repo openscad/)",
        default=None,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help="Directory to store rendered STLs (defaults to stl/static/)",
        default=None,
    )
    args = parser.parse_args(argv)

    rendered = render_static_stls(
        source_root=args.source_root,
        output_root=args.output_root,
    )

    for scad_path, stl_path in rendered:
        print(f"Rendered {stl_path} from {scad_path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - thin CLI
    return _cli(argv)


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
