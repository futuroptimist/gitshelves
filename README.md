# Gitshelves

[![Lint & Format](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/01-lint-format.yml?label=lint%20%26%20format)](https://github.com/futuroptimist/gitshelves/actions/workflows/01-lint-format.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/02-tests.yml?label=tests)](https://github.com/futuroptimist/gitshelves/actions/workflows/02-tests.yml)
[![Coverage](https://codecov.io/gh/futuroptimist/gitshelves/branch/main/graph/badge.svg)](https://codecov.io/gh/futuroptimist/gitshelves)
[![Docs](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/03-docs.yml?label=docs)](https://github.com/futuroptimist/gitshelves/actions/workflows/03-docs.yml)
[![License](https://img.shields.io/github/license/futuroptimist/gitshelves)](LICENSE)

Gitshelves fetches GitHub contribution data and turns it into 3D printable models. Each month of activity becomes a stack of blocks whose height is determined logarithmically by the number of contributions. The models are exported as `.scad` files for OpenSCAD and can be previewed with Three.js.

## Usage

1. Install the package in editable mode.
2. Run the CLI to generate a `.scad` file.

```bash
pip install -e .
python -m gitshelves.cli <github-username> --token <gh-token> \
    --start-year 2021 --end-year 2023 \
    --months-per-row 10 --stl contributions.stl
```

The command will create `contributions.scad` (and optionally `contributions.stl`) in the current directory. Months are arranged in rows of twelve by default, but you can choose the grid width via `--months-per-row`.

See [AGENTS.md](AGENTS.md) for agent workflow guidelines and additional docs under [docs/](docs/).
