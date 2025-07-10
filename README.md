# Gitshelves

Gitshelves fetches GitHub contribution data and turns it into 3D printable models. Each month of activity becomes a stack of blocks whose height is determined logarithmically by the number of contributions. The models are exported as `.scad` files for OpenSCAD and can be previewed with Three.js.

## Getting Started

Install the package in editable mode and run the CLI to generate a `.scad` file:

```bash
pip install -e .
python -m gitshelves.cli <github-username> --token <gh-token> \
    --start-year 2021 --end-year 2023
```

The command will create `contributions.scad` in the current directory.

The resulting model arranges months in a 1x12 grid for each year, stacked
side-by-side so multiple years fit on a single platform.

See [AGENTS.md](AGENTS.md) for agent workflow guidelines.

