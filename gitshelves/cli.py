import argparse
import os
from pathlib import Path
from datetime import datetime
from importlib import metadata, resources

from .fetch import fetch_user_contributions, _determine_year_range
from .scad import (
    generate_scad_monthly,
    generate_scad_monthly_levels,
    group_scad_levels,
    scad_to_stl,
)
from .readme import write_year_readme


BASEPLATE_FILENAME = "baseplate_2x6.scad"


def _baseplate_source() -> str:
    """Return the contents of the packaged baseplate template."""

    try:
        template = resources.files("gitshelves.data").joinpath(BASEPLATE_FILENAME)
    except (
        FileNotFoundError,
        ModuleNotFoundError,
    ) as exc:  # pragma: no cover - defensive
        raise FileNotFoundError(
            f"Missing baseplate template package: gitshelves.data/{BASEPLATE_FILENAME}"
        ) from exc
    if not template.is_file():
        raise FileNotFoundError(
            f"Missing baseplate template: gitshelves.data/{BASEPLATE_FILENAME}"
        )
    return template.read_text()


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
        choices=range(1, 5),
        default=1,
        help="Number of print colors (1-4)",
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

    token = args.token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    contribs = fetch_user_contributions(
        args.username,
        token=token,
        start_year=args.start_year,
        end_year=args.end_year,
    )

    counts = {}
    for item in contribs:
        d = item["created_at"][:10]
        dt = datetime.fromisoformat(d)
        key = (dt.year, dt.month)
        counts[key] = counts.get(key, 0) + 1

    start_year, end_year = _determine_year_range(args.start_year, args.end_year)
    for year in range(start_year, end_year + 1):
        write_year_readme(year, counts)

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
        base_output = Path(args.output)
        base_output.parent.mkdir(parents=True, exist_ok=True)
        if base_output.suffix:
            base_output = base_output.with_suffix("")
        base_stl = Path(args.stl) if args.stl else None
        if base_stl:
            base_stl.parent.mkdir(parents=True, exist_ok=True)
            if base_stl.suffix:
                base_stl = base_stl.with_suffix("")
        for idx, text in grouped.items():
            scad_path = base_output.with_name(f"{base_output.name}_color{idx}.scad")
            scad_path.write_text(text)
            print(f"Wrote {scad_path}")
            if base_stl:
                stl_path = base_stl.with_name(f"{base_stl.name}_color{idx}.stl")
                scad_to_stl(str(scad_path), str(stl_path))
                print(f"Wrote {stl_path}")

        baseplate_src = _baseplate_source()
        baseplate_dest = base_output.with_name(f"{base_output.name}_baseplate.scad")
        baseplate_dest.write_text(baseplate_src)
        print(f"Wrote {baseplate_dest}")
        if base_stl:
            baseplate_stl = base_stl.with_name(f"{base_stl.name}_baseplate.stl")
            scad_to_stl(str(baseplate_dest), str(baseplate_stl))
            print(f"Wrote {baseplate_stl}")


if __name__ == "__main__":
    main()
