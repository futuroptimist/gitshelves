# Gitshelves

[![Lint & Format](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/01-lint-format.yml?label=lint%20%26%20format)](https://github.com/futuroptimist/gitshelves/actions/workflows/01-lint-format.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/02-tests.yml?label=tests)](https://github.com/futuroptimist/gitshelves/actions/workflows/02-tests.yml)
[![Coverage](https://codecov.io/gh/futuroptimist/gitshelves/branch/main/graph/badge.svg)](https://codecov.io/gh/futuroptimist/gitshelves)
[![Docs](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/03-docs.yml?label=docs)](https://github.com/futuroptimist/gitshelves/actions/workflows/03-docs.yml)
[![License](https://img.shields.io/github/license/futuroptimist/gitshelves)](LICENSE)

Gitshelves fetches GitHub contribution data and turns it into 3D printable models. Each month of activity becomes a stack of blocks whose height is determined logarithmically by the number of contributions. The models are exported as `.scad` files for OpenSCAD and can be previewed with Three.js.

A simple wall shelf with drywall mounting holes lives in `openscad/shelf.scad`. Use the pre-rendered `stl/shelf.stl` to print a matching display shelf for your contribution charts.


`load_baseplate_scad()` ships both the 2×6 Gridfinity plate and a packaged `baseplate_1x12.scad` for tall single-row layouts, so
you can source narrow baseplates without cloning the OpenSCAD sources.

## Usage

1. Install the package in editable mode.
2. Generate a [personal access token][token-doc] with `public_repo` scope. Export
   it as `GH_TOKEN` for local use or rely on `GITHUB_TOKEN` in CI.
3. Run the CLI to generate a `.scad` file. If `--token` is omitted, the CLI reads
   `GH_TOKEN` then `GITHUB_TOKEN`. `fetch_user_contributions` uses the same
   fallback order when no token argument is supplied.
   Without `--start-year` and `--end-year`, only the current year's
   contributions are included.

[token-doc]: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token

```bash
pip install -e .
export GH_TOKEN=<your-token>  # or GITHUB_TOKEN
python -m gitshelves.cli <github-username> \
    --start-year 2021 --end-year 2023 \
    --months-per-row 10 --stl contributions.stl --colors 1
```

The command creates `contributions.scad` (and optionally `contributions.stl`)
in the current directory. The example sets `--months-per-row 10`; omit this
flag to keep the default of 12 months per row. Use `--output` to pick a
different `.scad` filename.

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

Print the current version with:

```bash
python -m gitshelves.cli --version
```

Use `--colors` to control multi-color outputs. `--colors 2` produces one block file and a baseplate for two-color prints. `--colors 3` or `4` group logarithmic levels into additional color files, and `--colors 5` separates the levels into four distinct block colors. Each `*_colorN.scad` (`*_colorN.stl`) contains the blocks for a color group, and the baseplate is written as `<name>_baseplate.scad` (and `.stl` when requested). When contribution counts span more than four logarithmic levels, the fourth color collects the remaining higher magnitudes so extra orders reuse the accent color.
Lower magnitudes stay in the earliest `color` files, and any surplus levels beyond the available
groups are appended to the final `color` output so accent-colored cubes repeat for larger orders of
magnitude. `group_scad_levels` enforces this by keeping the first three levels in their own groups and
funneling all higher orders into the fourth group whenever five colors are requested, so the accent
color consistently represents the highest magnitudes.

For print tuning tips—including slicer presets for baseplates and cubes plus AMS
automation snippets—see [docs/usage.md](docs/usage.md).

Pass `--gridfinity-layouts` to emit a parametric `stl/<year>/gridfinity_plate.scad` that builds a
Gridfinity baseplate and arranges monthly contribution cubes on top of it. The layout defaults to six
columns (a 2×6 plate); adjust the footprint with `--gridfinity-columns` to match your storage grid.
When `--stl` is supplied, the CLI also renders `stl/<year>/gridfinity_plate.stl` so the baseplate is
ready to print alongside the contribution cubes. Pair it with `--gridfinity-cubes` to generate
`contrib_cube_MM.scad` and `.stl` stacks for every month that recorded contributions so cube prints are
ready without extra modeling work.

Open [docs/viewer.html](docs/viewer.html) in a browser to preview generated STL files with
[Three.js](https://threejs.org/) and experiment with different color counts. Use the file
picker to load your baseplate and `_colorN` (or legacy `levelN`) STLs—the viewer
automatically maps these names back to the color groups that the CLI generates, shows a
detected block-color count next to the picker, and updates the Colors dropdown to match the
files. Adjusting the dropdown now hides higher block-color groups so you can quickly preview
how the model looks when you print with fewer colors, while still keeping manual selection
optional.

If you fork this repository, replace `futuroptimist` with your GitHub username in badge URLs to keep status badges working.

```
# = block (higher stacks mean more contributions)

  #      ##     ###
  #      ##     ###
         ##     ###
```

See [AGENTS.md](AGENTS.md) for agent workflow guidelines and
[docs](docs/index.md) for additional documentation.

## Dependencies

- [Gridfinity-Rebuilt-OpenSCAD](https://github.com/kennetek/gridfinity-rebuilt-openscad) –
  parametric Gridfinity modules. The CI workflow clones this repo into
  `openscad/lib/gridfinity-rebuilt` when building STL files.
- [OpenSCAD](https://openscad.org/) ≥ 2024.06 – required to render STL files. Install
  `xvfb-run` on headless systems; the `scad_to_stl` helper wraps OpenSCAD with it
  automatically when `$DISPLAY` is missing, mirroring the CI workflow.
- [vector76/gridfinity_openscad](https://github.com/vector76/gridfinity_openscad) – reference
  implementation we consult for specification details (MIT).

## How to Build Locally

```bash
# Clone the Gridfinity library locally (the CI workflow does this automatically)
git clone https://github.com/kennetek/gridfinity-rebuilt-openscad \
    openscad/lib/gridfinity-rebuilt
# `scad_to_stl` automatically wraps `openscad` in `xvfb-run` when `$DISPLAY`
# is unset or empty and exports binary STLs (`--export-format binstl`) to match
# the CI configuration. Ensure `xvfb-run` is installed on headless systems.
openscad -o stl/2024/baseplate_2x6.stl \
    --export-format binstl openscad/baseplate_2x6.scad
```

Run `black --check .`, `pytest -q`, and `codespell docs README.md` before submitting
changes. Add project-specific terms to `dict/allow.txt`.

## STL Build Outputs

The `build-stl` workflow runs on every push and pull request targeting `main`
and attaches the rendered STL files as downloadable artifacts. Navigate to the
workflow run and download `stl-<year>` to obtain the converted models.
To avoid bloating the repository, pre-generated baseplate models are no longer stored in the repo. Download the `stl-<year>` artifact or generate them locally.
Each `stl/<year>` directory includes a generated `README.md` summarizing the baseplate and monthly
cube counts. The CLI writes these summaries for every year in the requested range, even when a year
has no contributions, so your shelf layout stays predictable.
Day-level views are also written to `stl/<year>/monthly-5x6/` as OpenSCAD files. Each calendar lays
out the month's days in rows of five to stay within a 256 mm square build area, adding a partial row
for 31-day months.
Monthly `.scad` exports reserve slots for every month in the requested range as well, so years without
activity remain in place—they simply render zero-height stacks until you contribute again.
Months without contributions are annotated in the SCAD output so you can confirm each slot's
position when previewing or editing the file.
## Troubleshooting

OpenSCAD exits with status 1 when it cannot access an X display. The
`scad_to_stl` helper wraps the command in `xvfb-run` when `$DISPLAY` is
unset or empty. Install `xvfb-run` if you still encounter this error on a headless
machine.
