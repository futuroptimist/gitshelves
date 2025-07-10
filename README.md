# Gitshelves

Gitshelves fetches GitHub contribution data and turns it into 3D printable models. Each day of activity becomes a stack of blocks whose height is determined logarithmically by the number of contributions. The models are exported as `.scad` files for OpenSCAD and can be previewed with Three.js.

## Getting Started

Install the package in editable mode and run the CLI to generate a `.scad` file:

```bash
pip install -e .
python -m gitshelves.cli <github-username> --token <gh-token>
```

The command will create `contributions.scad` in the current directory.

See [AGENTS.md](AGENTS.md) for agent workflow guidelines.

