from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Dict, Sequence, Tuple

from .scad import blocks_for_contributions


def write_year_readme(
    year: int,
    counts: Dict[Tuple[int, int], int],
    outdir: Path | str = Path("stl"),
    extras: Sequence[str] | None = None,
    *,
    include_baseplate_stl: bool = False,
    calendar_slug: str = "monthly-12x6",
) -> Path:
    """Write a README detailing materials for ``year``.

    A summary of the baseplate STL and monthly cube counts is written to
    ``stl/<year>/README.md``. Optional ``extras`` entries append additional
    bullet points (for example Gridfinity outputs). Set
    ``include_baseplate_stl`` to ``True`` when a rendered baseplate STL is
    available so the README links to both artifacts. ``calendar_slug`` names
    the directory that stores the per-day calendar exports (for example
    ``monthly-12x6`` when twelve days share a row by default). The function returns
    the path to the created file.
    """
    path = Path(outdir) / str(year)
    path.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# {year} Materials",
        "",
        "## Baseplate",
        "- [`baseplate_2x6.scad`](baseplate_2x6.scad)",
    ]
    if include_baseplate_stl:
        lines.append("- [`baseplate_2x6.stl`](baseplate_2x6.stl)")

    lines += [
        "",
        "## Monthly Cubes",
    ]
    for month in range(1, 13):
        count = counts.get((year, month), 0)
        cubes = blocks_for_contributions(count)
        name = datetime(year, month, 1).strftime("%B")
        lines.append(
            f"- {name}: {count} contribution{'s' if count != 1 else ''} \u2192 {cubes} cube{'s' if cubes != 1 else ''}"
        )

    lines += [
        "",
        "## Versions",
        (
            f"- `{calendar_slug}`: daily calendars in [`{calendar_slug}/`]({calendar_slug}) "
            "that fit a 256 mm square bed"
        ),
    ]

    if extras:
        lines += ["", "## Gridfinity"]
        lines.extend(extras)

    readme_path = path / "README.md"
    readme_path.write_text("\n".join(lines))
    return readme_path
