# Gitshelves

[![Lint & Format](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/01-lint-format.yml?label=lint%20%26%20format)](https://github.com/futuroptimist/gitshelves/actions/workflows/01-lint-format.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/02-tests.yml?label=tests)](https://github.com/futuroptimist/gitshelves/actions/workflows/02-tests.yml)
[![Coverage](https://codecov.io/gh/futuroptimist/gitshelves/branch/main/graph/badge.svg)](https://codecov.io/gh/futuroptimist/gitshelves)
[![Docs](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/03-docs.yml?label=docs)](https://github.com/futuroptimist/gitshelves/actions/workflows/03-docs.yml)
[![License](https://img.shields.io/github/license/futuroptimist/gitshelves)](LICENSE)

Gitshelves fetches GitHub contribution data and turns it into 3D printable models. Each month of activity becomes a stack of blocks whose height is determined logarithmically by the number of contributions. The models are exported as `.scad` files for OpenSCAD and can be previewed with Three.js.

## Usage

1. Install the package in editable mode.
2. Generate a [personal access token](https://github.com/settings/tokens) and export it as
   `GH_TOKEN`.
3. Run the CLI to generate a `.scad` file. The token is read from `GH_TOKEN` or
   `GITHUB_TOKEN` if `--token` is omitted.
   `fetch_user_contributions` likewise falls back to these variables when
   no token argument is supplied.

```bash
pip install -e .
export GH_TOKEN=<your-token>
python -m gitshelves.cli <github-username> \
    --start-year 2021 --end-year 2023 \
    --months-per-row 10 --stl contributions.stl --colors 1
```

The command will create `contributions.scad` (and optionally `contributions.stl`) in the current directory. Months are arranged in rows of twelve by default, but you can choose the grid width via `--months-per-row`.

For instance, `--months-per-row 8` lays out eight months per row:

```bash
python -m gitshelves.cli <github-username> --token "$GH_TOKEN" \
    --start-year 2024 --end-year 2024 --months-per-row 8
```

This produces a grid with eight columns on the first row and the remaining months below:

```
Jan Feb Mar Apr May Jun Jul Aug
Sep Oct Nov Dec
```

Use `--colors` to control multi-color outputs. `--colors 2` produces one blocks file and a baseplate for two-color prints. `--colors 3` or `4` group logarithmic levels into additional color files. Each `*_colorN.scad` (`*_colorN.stl`) contains the blocks for a color group.

Open [docs/viewer.html](docs/viewer.html) in a browser to preview generated STL files with
Three.js and experiment with different color counts.
Use the file picker to load your baseplate and level STLs.

If you fork this repository, replace `futuroptimist` with your GitHub username in badge URLs to keep status badges working.

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
- [vector76/gridfinity_openscad](https://github.com/vector76/gridfinity_openscad) – reference implementation we consult for specification details (MIT).

## How to Build Locally

```bash
# Clone the Gridfinity library locally (the CI workflow does this automatically)
git clone https://github.com/kennetek/gridfinity-rebuilt-openscad \
    openscad/lib/gridfinity-rebuilt
# `scad_to_stl` automatically wraps `openscad` in `xvfb-run` when `$DISPLAY`
# is unset or empty, matching the CI configuration. Ensure `xvfb-run` is
# installed on headless systems.
openscad -o stl/2024/baseplate_2x6.stl openscad/baseplate_2x6.scad
```

Run `black --check .`, `pytest -q`, and `codespell docs README.md` before submitting
changes. Add project-specific terms to `dict/allow.txt`.

## STL Build Outputs

The `build-stl` workflow runs on every push and pull request targeting `main`
and attaches the rendered STL files as downloadable artifacts. Navigate to the
workflow run and download `stl-<year>` to obtain the converted models.
To avoid bloating the repository, pre-generated baseplate models are no longer stored in the repo. Download the `stl-<year>` artifact or generate them locally.
Each `stl/<year>` directory includes a generated `README.md` summarizing the baseplate and monthly cube counts.
## Troubleshooting

OpenSCAD exits with status 1 when it cannot access an X display. The
`scad_to_stl` helper wraps the command in `xvfb-run` when `$DISPLAY` is
unset or empty. Install `xvfb-run` if you still encounter this error on a headless
machine.
