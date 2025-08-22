from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

from .scad import blocks_for_contributions


def write_year_readme(
    year: int,
    counts: Dict[Tuple[int, int], int],
    outdir: Path | str = Path("stl"),
) -> Path:
    """Write a README detailing materials for ``year``.

    A summary of the baseplate STL and monthly cube counts is written to
    ``stl/<year>/README.md``. The function returns the path to the created file.
    """
    path = Path(outdir) / str(year)
    path.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# {year} Materials",
        "",
        "## Baseplate",
        "- [`baseplate_2x6.stl`](baseplate_2x6.stl)",
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
        "- `monthly-5x6`: zoomed view of days per month in 5×6 grid (256 mm³)",
    ]

    readme_path = path / "README.md"
    readme_path.write_text("\n".join(lines))
    return readme_path
