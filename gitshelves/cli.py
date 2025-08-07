import argparse
from pathlib import Path
from datetime import datetime

from .fetch import fetch_user_contributions
from .scad import (
    generate_scad_monthly,
    generate_scad_monthly_levels,
    group_scad_levels,
    scad_to_stl,
)
from .readme import write_year_readme


def main():
    parser = argparse.ArgumentParser(
        description="Generate 3D GitHub contribution charts"
    )
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("--token", help="GitHub API token")
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
    args = parser.parse_args()

    contribs = fetch_user_contributions(
        args.username,
        token=args.token,
        start_year=args.start_year,
        end_year=args.end_year,
    )

    counts = {}
    for item in contribs:
        d = item["created_at"][:10]
        dt = datetime.fromisoformat(d)
        key = (dt.year, dt.month)
        counts[key] = counts.get(key, 0) + 1

    for year in {y for y, _ in counts}:
        write_year_readme(year, counts)

    if args.colors == 1:
        scad_text = generate_scad_monthly(counts, months_per_row=args.months_per_row)
        Path(args.output).write_text(scad_text)
        print(f"Wrote {args.output}")
        if args.stl:
            scad_to_stl(str(Path(args.output)), str(Path(args.stl)))
            print(f"Wrote {args.stl}")
    else:
        level_scads = generate_scad_monthly_levels(
            counts, months_per_row=args.months_per_row
        )
        grouped = group_scad_levels(
            level_scads, args.colors - 1 if args.colors > 1 else 1
        )
        base_output = Path(args.output)
        if base_output.suffix:
            base_output = base_output.with_suffix("")
        base_stl = Path(args.stl) if args.stl else None
        if base_stl and base_stl.suffix:
            base_stl = base_stl.with_suffix("")
        for idx, text in grouped.items():
            scad_path = base_output.with_name(f"{base_output.name}_color{idx}.scad")
            scad_path.write_text(text)
            print(f"Wrote {scad_path}")
            if base_stl:
                stl_path = base_stl.with_name(f"{base_stl.name}_color{idx}.stl")
                scad_to_stl(str(scad_path), str(stl_path))
                print(f"Wrote {stl_path}")


if __name__ == "__main__":
    main()
