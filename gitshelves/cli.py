import argparse
from pathlib import Path
from datetime import datetime

from .fetch import fetch_user_contributions
from .scad import generate_scad_monthly


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

    scad_text = generate_scad_monthly(counts)
    Path(args.output).write_text(scad_text)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
