import argparse
import os
from calendar import month_name
from pathlib import Path
from datetime import datetime
from importlib import metadata

from .baseplate import load_baseplate_scad
from .fetch import fetch_user_contributions, _determine_year_range
from .scad import (
    blocks_for_contributions,
    generate_contrib_cube_stack_scad,
    generate_scad_monthly,
    generate_scad_monthly_levels,
    generate_monthly_calendar_scads,
    generate_gridfinity_plate_scad,
    generate_zero_month_annotations,
    group_scad_levels,
    scad_to_stl,
)
from .readme import write_year_readme


def _write_year_baseplate(year_dir: Path, render_stl: bool) -> None:
    """Copy the bundled 2×6 baseplate into ``year_dir`` and optionally render an STL."""

    year_dir.mkdir(parents=True, exist_ok=True)
    baseplate_path = year_dir / "baseplate_2x6.scad"
    baseplate_text = load_baseplate_scad("baseplate_2x6.scad")
    baseplate_path.write_text(baseplate_text)
    print(f"Wrote {baseplate_path}")
    if render_stl:
        baseplate_stl = baseplate_path.with_suffix(".stl")
        scad_to_stl(str(baseplate_path), str(baseplate_stl))
        print(f"Wrote {baseplate_stl}")


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Generate 3D GitHub contribution charts"
    )
    parser.add_argument("username", help="GitHub username")
    parser.add_argument(
        "--token",
        help="GitHub API token (defaults to GH_TOKEN or GITHUB_TOKEN env vars)",
    )
    parser.add_argument("--start-year", type=int, help="First year of contributions")
    parser.add_argument("--end-year", type=int, help="Last year of contributions")
    parser.add_argument(
        "--output", default="contributions.scad", help="Output .scad file"
    )
    parser.add_argument(
        "--months-per-row",
        type=int,
        default=12,
        help="Number of months displayed across each row",
    )
    parser.add_argument(
        "--stl",
        help="Optional output STL file (requires openscad)",
    )
    parser.add_argument(
        "--colors",
        type=int,
        choices=range(1, 6),
        default=1,
        help="Number of print colors (1-5)",
    )
    parser.add_argument(
        "--gridfinity-layouts",
        action="store_true",
        help="Generate Gridfinity baseplate layouts per year",
    )
    parser.add_argument(
        "--gridfinity-columns",
        type=int,
        default=6,
        help="Columns per Gridfinity baseplate row when layouts are generated",
    )
    parser.add_argument(
        "--gridfinity-cubes",
        action="store_true",
        help="Generate monthly Gridfinity cube stacks (SCAD; add --stl for STLs)",
    )
    parser.add_argument(
        "--baseplate-template",
        choices=["baseplate_2x6.scad", "baseplate_1x12.scad"],
        default="baseplate_2x6.scad",
        help="Bundled baseplate template to copy when generating multi-color outputs",
    )
    try:  # pragma: no cover - metadata lookup
        pkg_version = metadata.version("gitshelves")
    except metadata.PackageNotFoundError:  # pragma: no cover
        pkg_version = "0.0.0"
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {pkg_version}"
    )
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(argv)

    if args.gridfinity_columns <= 0:
        parser.error("--gridfinity-columns must be positive")

    if not hasattr(args, "baseplate_template"):
        args.baseplate_template = "baseplate_2x6.scad"

    token = args.token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    contribs = fetch_user_contributions(
        args.username,
        token=token,
        start_year=args.start_year,
        end_year=args.end_year,
    )

    counts = {}
    daily_counts = {}
    for item in contribs:
        d = item["created_at"][:10]
        dt = datetime.fromisoformat(d)
        key = (dt.year, dt.month)
        counts[key] = counts.get(key, 0) + 1
        day_key = (dt.year, dt.month, dt.day)
        daily_counts[day_key] = daily_counts.get(day_key, 0) + 1

    start_year, end_year = _determine_year_range(args.start_year, args.end_year)
    counts = {
        (year, month): counts.get((year, month), 0)
        for year in range(start_year, end_year + 1)
        for month in range(1, 13)
    }

    render_yearly_stl = bool(args.stl)
    for year in range(start_year, end_year + 1):
        readme_path = write_year_readme(year, counts)
        year_dir = readme_path.parent
        _write_year_baseplate(year_dir, render_yearly_stl)
        calendars = generate_monthly_calendar_scads(daily_counts, year)
        calendar_dir = year_dir / "monthly-5x6"
        calendar_dir.mkdir(parents=True, exist_ok=True)
        for month, text in calendars.items():
            slug = month_name[month].lower()
            scad_path = calendar_dir / f"{month:02d}_{slug}.scad"
            scad_path.write_text(text)
            print(f"Wrote {scad_path}")
        if args.gridfinity_layouts:
            layout_text = generate_gridfinity_plate_scad(
                counts, year, columns=args.gridfinity_columns
            )
            layout_path = readme_path.parent / "gridfinity_plate.scad"
            layout_path.write_text(layout_text)
            print(f"Wrote {layout_path}")
            if args.stl:
                layout_stl_path = layout_path.with_suffix(".stl")
                scad_to_stl(str(layout_path), str(layout_stl_path))
                print(f"Wrote {layout_stl_path}")
        if args.gridfinity_cubes:
            year_dir = readme_path.parent
            for month in range(1, 13):
                levels = blocks_for_contributions(counts.get((year, month), 0))
                if levels <= 0:
                    continue
                cube_scad = generate_contrib_cube_stack_scad(levels)
                cube_scad_path = year_dir / f"contrib_cube_{month:02d}.scad"
                cube_scad_path.write_text(cube_scad)
                print(f"Wrote {cube_scad_path}")
                if args.stl:
                    cube_stl_path = cube_scad_path.with_suffix(".stl")
                    scad_to_stl(str(cube_scad_path), str(cube_stl_path))
                    print(f"Wrote {cube_stl_path}")

    if args.colors == 1:
        scad_text = generate_scad_monthly(counts, months_per_row=args.months_per_row)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(scad_text)
        print(f"Wrote {output_path}")
        if args.stl:
            stl_path = Path(args.stl)
            stl_path.parent.mkdir(parents=True, exist_ok=True)
            scad_to_stl(str(output_path), str(stl_path))
            print(f"Wrote {stl_path}")
    else:
        level_scads = generate_scad_monthly_levels(
            counts, months_per_row=args.months_per_row
        )
        grouped = group_scad_levels(
            level_scads, args.colors - 1 if args.colors > 1 else 1
        )
        zero_comments = generate_zero_month_annotations(
            counts, months_per_row=args.months_per_row
        )
        base_output = Path(args.output)
        base_output.parent.mkdir(parents=True, exist_ok=True)
        if base_output.suffix:
            base_output = base_output.with_suffix("")
        base_stl = Path(args.stl) if args.stl else None
        if base_stl:
            base_stl.parent.mkdir(parents=True, exist_ok=True)
            if base_stl.suffix:
                base_stl = base_stl.with_suffix("")
        baseplate_path = base_output.with_name(f"{base_output.name}_baseplate.scad")
        try:
            baseplate_source = load_baseplate_scad(args.baseplate_template)
        except TypeError:
            baseplate_source = load_baseplate_scad()
        baseplate_path.write_text(baseplate_source)
        print(f"Wrote {baseplate_path}")
        if base_stl:
            baseplate_stl = base_stl.with_name(f"{base_stl.name}_baseplate.stl")
            scad_to_stl(str(baseplate_path), str(baseplate_stl))
            print(f"Wrote {baseplate_stl}")
        for idx, text in grouped.items():
            scad_path = base_output.with_name(f"{base_output.name}_color{idx}.scad")
            lines = text.splitlines()
            if zero_comments:
                if lines and lines[-1].strip():
                    lines.append("")
                lines.extend(zero_comments)
            scad_output = "\n".join(lines)
            scad_path.write_text(scad_output)
            print(f"Wrote {scad_path}")
            if base_stl:
                stl_path = base_stl.with_name(f"{base_stl.name}_color{idx}.stl")
                scad_to_stl(str(scad_path), str(stl_path))
                print(f"Wrote {stl_path}")


if __name__ == "__main__":
    main()
