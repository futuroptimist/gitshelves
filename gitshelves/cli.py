import argparse
import json
from pathlib import Path

from .fetch import fetch_user_contributions
from .scad import generate_scad


def main():
    parser = argparse.ArgumentParser(description="Generate 3D GitHub contribution charts")
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("--token", help="GitHub API token")
    parser.add_argument("--output", default="contributions.scad", help="Output .scad file")
    args = parser.parse_args()

    contribs = fetch_user_contributions(args.username, token=args.token)

    dates = [item["created_at"][:10] for item in contribs]
    counts = {}
    for d in dates:
        counts[d] = counts.get(d, 0) + 1
    days_sorted = sorted(counts.keys())
    daily_counts = [counts[d] for d in days_sorted]

    scad_text = generate_scad(daily_counts)
    Path(args.output).write_text(scad_text)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
