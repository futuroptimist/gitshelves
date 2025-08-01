# Gitshelves

[![Lint & Format](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/01-lint-format.yml?label=lint%20%26%20format)](https://github.com/futuroptimist/gitshelves/actions/workflows/01-lint-format.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/02-tests.yml?label=tests)](https://github.com/futuroptimist/gitshelves/actions/workflows/02-tests.yml)
[![Coverage](https://codecov.io/gh/futuroptimist/gitshelves/branch/main/graph/badge.svg)](https://codecov.io/gh/futuroptimist/gitshelves)
[![Docs](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/03-docs.yml?label=docs)](https://github.com/futuroptimist/gitshelves/actions/workflows/03-docs.yml)
[![License](https://img.shields.io/github/license/futuroptimist/gitshelves)](LICENSE)

Gitshelves fetches GitHub contribution data and turns it into 3D printable models. Each month of activity becomes a stack of blocks whose height is determined logarithmically by the number of contributions. The models are exported as `.scad` files for OpenSCAD and can be previewed with Three.js.

## Usage

1. Install the package in editable mode.
2. Generate a personal access token from GitHub ("Settings → Developer settings → Personal access tokens") and assign it to `GH_TOKEN`.
3. Run the CLI to generate a `.scad` file.

```bash
GH_TOKEN=<your-token>
```

```bash
pip install -e .
python -m gitshelves.cli <github-username> --token "$GH_TOKEN" \
    --start-year 2021 --end-year 2023 \
    --months-per-row 10 --stl contributions.stl
```

The command will create `contributions.scad` (and optionally `contributions.stl`) in the current directory. Months are arranged in rows of twelve by default, but you can choose the grid width via `--months-per-row`.

```
# = block (higher stacks mean more contributions)

  #      ##     ###
  #      ##     ###
         ##     ###
```

See [AGENTS.md](AGENTS.md) for agent workflow guidelines and additional docs under [docs/](docs/).

## Dependencies

 - [Gridfinity-Rebuilt-OpenSCAD](https://github.com/kennetek/gridfinity-rebuilt-openscad) – parametric Gridfinity modules. The CI workflow clones this repo into `openscad/lib/gridfinity-rebuilt` when building STL files.
- [OpenSCAD](https://openscad.org/) ≥ 2024.06 – required to render STL files.
- GitHub Actions installs `openscad` with `xvfb` to convert `.scad` sources to binary STL outputs in a headless environment.

## How to Build Locally

```bash
# Clone the Gridfinity library locally (the CI workflow does this automatically)
git clone https://github.com/kennetek/gridfinity-rebuilt-openscad \
    openscad/lib/gridfinity-rebuilt
# `scad_to_stl` automatically wraps `openscad` in `xvfb-run` when `$DISPLAY`
# is missing, matching the CI configuration. Ensure `xvfb-run` is installed on
# headless systems.
openscad -o stl/2024/baseplate_1x12.stl openscad/baseplate_1x12.scad
```

Run `black --check .` and `pytest -q` before submitting changes.

## STL Build Outputs

The `build-stl` workflow runs on every push to `main` and attaches the rendered
STL files as downloadable artifacts. Navigate to the workflow run and download
`stl-<year>` to obtain the converted models.
## Troubleshooting

OpenSCAD exits with status 1 when it cannot access an X display. The
`scad_to_stl` helper wraps the command in `xvfb-run` when `$DISPLAY` is
missing. Install `xvfb-run` if you still encounter this error on a headless
machine.
