# Gitshelves

[![Lint & Format](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/01-lint-format.yml?label=lint%20%26%20format)](https://github.com/futuroptimist/gitshelves/actions/workflows/01-lint-format.yml)
[![Tests](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/02-tests.yml?label=tests)](https://github.com/futuroptimist/gitshelves/actions/workflows/02-tests.yml)
[![Coverage](https://codecov.io/gh/futuroptimist/gitshelves/branch/main/graph/badge.svg)](https://codecov.io/gh/futuroptimist/gitshelves)
[![Docs](https://img.shields.io/github/actions/workflow/status/futuroptimist/gitshelves/.github/workflows/03-docs.yml?label=docs)](https://github.com/futuroptimist/gitshelves/actions/workflows/03-docs.yml)
[![License](https://img.shields.io/github/license/futuroptimist/gitshelves)](LICENSE)

Gitshelves fetches GitHub contribution data and turns it into 3D printable models. Each month of activity becomes a stack of blocks whose height is determined logarithmically by the number of contributions. The models are exported as `.scad` files for OpenSCAD and can be previewed with Three.js.

A simple wall shelf with drywall mounting holes lives in `openscad/shelf.scad`. Use the pre-rendered `stl/shelf.stl` to print a matching display shelf for your contribution charts.


`load_baseplate_scad()` ships both the 2×6 Gridfinity plate and a packaged `baseplate_1x12.scad`
for tall single-row layouts, so you can source narrow baseplates without cloning the OpenSCAD
sources. If the packaged data is unavailable or unreadable, it automatically falls back to the
matching templates in `openscad/` so source checkouts stay functional.

## Usage

1. Install the package in editable mode.
2. Generate a [personal access token][token-doc] with `public_repo` scope. Export
   it as `GH_TOKEN` for local use or rely on `GITHUB_TOKEN` in CI.
3. Run the CLI to generate a `.scad` file. Authentication tokens resolve in the
   following order: explicit `--token` argument, `GH_TOKEN`, then `GITHUB_TOKEN`.
   `fetch_user_contributions` uses the same fallback order when no token
   argument is supplied.
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
in the current directory. Runs without `--stl` delete any lingering
`contributions.stl` mesh so the directory mirrors the current invocation,
even when older metadata has been removed. The
example sets `--months-per-row 10`; omit this flag to keep the default of 12
months per row. Use `--output` to pick a
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

### Metadata exports

Every generated `.scad` file now ships with a sibling `.json` metadata document. The
JSON records the CLI arguments that influence geometry (color count, Gridfinity
flags, baseplate template, calendar spacing), the resolved year range, and the
output paths for the SCAD/STL pair. Monthly and daily contribution counts are
embedded so downstream tooling can render previews or perform comparisons without
re-parsing the SCAD source. The metadata includes an `"stl_generated"` flag and
stores `null` in `"stl"` when no mesh is produced so STL omissions are explicit.
For multi-color runs, `"colors"` preserves the requested palette size while
`"color_groups"` notes the actual block group count (capped at four) so automation
can detect when accent levels are consolidated. When only a subset of the palette
contains geometry, the metadata records that smaller `"color_groups"` value (for
example, a five-color run with two populated levels reports `"color_groups": 2`).
Stacks that reach higher magnitudes still populate the lower logarithmic levels,
and the metadata reflects that by reporting the highest occupied level even when
every month lands in the same magnitude—three-block stacks still contribute three
color groups, for instance.
Color-specific metadata now mirrors the SCAD annotations by listing `"zero_months"`
so placeholder `_colorN.scad` files still report which months occupy each slot even
when no blocks are printed.
Gridfinity layout metadata also
captures the detected footprint by recording both the configured column count and the
derived row total, allowing automation to recover the plate dimensions without parsing
README summaries. The run-level metadata summary mirrors this by exposing the computed
row count under `gridfinity.rows`, even when layout exports are skipped, so downstream
tools can infer the footprint without inspecting each layout record.

Pass `--json run-summary.json` to capture a run-level summary alongside the per-file
metadata. The summary records every generated SCAD file, its STL counterpart
(when present), and the path to the associated metadata document so downstream
tooling can ingest a single JSON payload.

Values below one trigger a parser error before any files are written, keeping invalid
`--months-per-row` settings from generating partial outputs. When you omit
`--calendar-days-per-row`, the CLI mirrors the monthly grid width (matching the value passed to
`--months-per-row` and defaulting to `monthly-12x6`). Pass `--calendar-days-per-row`
to override that width; the generated directories always follow the
`monthly-{days_per_row}x6` naming pattern while leaving the monthly summary grid
untouched.

Print the current version with:

```bash
python -m gitshelves.cli --version
```

Use `--colors` to control multi-color outputs. `--colors 2` splits blocks between
`*_color1.scad` and `*_color2.scad` while also writing `<name>_baseplate.scad` for the baseplate.
`--colors 3` and `--colors 4` add `*_color3.scad` and `*_color4.scad` so up to four block groups are
generated, and `--colors 5` keeps the same four block colors while reusing the accent file for any
additional logarithmic levels. Smaller palettes balance the logarithmic levels across the available
groups while preserving their chronological order, so `--colors 2`, `--colors 3`, and `--colors 4`
spread stacks as evenly as possible before the accent color kicks in. Each `*_colorN.scad`
(`*_colorN.stl`) contains the blocks for a color group, and the baseplate is written as
`<name>_baseplate.scad` (and `.stl` when requested). When contribution counts span more than four
logarithmic levels, the fourth color collects the remaining higher magnitudes so extra orders reuse
the accent color. Values outside the documented 1–5 range trigger a parser error before any files
are written.
Lower magnitudes stay in the earliest `color` files, and any surplus levels beyond the available
groups are appended to the final `color` output so accent-colored cubes repeat for larger orders
of magnitude. `group_scad_levels` enforces this by keeping the first three levels in their own
groups and funneling all higher orders into the fourth group whenever five colors are requested,
so the accent color consistently represents the highest magnitudes.
Switching to multi-color runs removes any lingering combined `<name>.scad` or `.stl` so the
`_colorN` exports fully replace the single-color block output, mirroring the CLI matrix.
Even when intermediate logarithmic levels are missing, `_color4` still gathers the remaining high
orders so the accent file continues to flag the peak activity.
Pass `--baseplate-template baseplate_1x12.scad`
to copy the bundled tall single-row Gridfinity baseplate when generating multi-color outputs; the
default template remains `baseplate_2x6.scad`. Every color-group SCAD repeats the zero-contribution
annotations, so layouts stay traceable even when you only open a subset of the color files.
Whether a run produces no blocks at all or only fills a subset of the requested color groups, the CLI
still emits `_colorN.scad` placeholders populated with the zero-contribution annotations so downstream
workflows keep the expected file set; STL rendering is skipped for those empty groups, and any existing
`_colorN.stl` meshes are deleted so unused groups leave no stale geometry behind.
When you reduce the palette, stale `_colorN.scad` files above the requested range are removed alongside
those `_colorN.stl` meshes (and every `_colorN.stl` is purged when `--stl` isn't requested) so follow-on
jobs only see the current color set. Switching to multi-color outputs removes the unified `<name>.scad`
export and its metadata so only the `_colorN` files remain. Returning to single-color runs with `--colors 1`
clears any lingering `_colorN` SCAD/STL files, leaving only the combined contribution export. Single-color
reruns also delete the matching `_baseplate` SCAD/STL pair from earlier multi-color runs so the directory
truly returns to the single-file layout.

For print tuning tips—including slicer presets for baseplates and cubes plus AMS
automation snippets—see [docs/usage.md](docs/usage.md).

Pass `--gridfinity-layouts` to emit a parametric `stl/<year>/gridfinity_plate.scad` that builds a
Gridfinity baseplate and arranges monthly contribution cubes on top of it. The layout defaults to six
columns (a 2×6 plate); adjust the footprint with `--gridfinity-columns` to match your storage grid.
The column count must be a positive integer—values below one are rejected before any files are written.
When `--stl` is supplied, the CLI also renders `stl/<year>/gridfinity_plate.stl` so the baseplate is
ready to print alongside the contribution cubes. Runs that omit `--stl` delete any existing
`gridfinity_plate.stl` meshes so the directory mirrors the current invocation. Re-running without `--gridfinity-layouts` removes
any previously generated `gridfinity_plate.scad`/`.stl` pairs so stale layouts do not linger. Pair it
with `--gridfinity-cubes` to generate `contrib_cube_MM.scad` stacks for every month that recorded
contributions. The CLI always renders matching `contrib_cube_MM.stl` meshes when this flag is enabled,
even if you omit `--stl`, so install `openscad` on systems that generate cube stacks. Printed sets stay
in sync automatically because each stack's SCAD and STL export are produced together on every run.
Empty months are still annotated in the Gridfinity layout as reserved grid cells, keeping the
placement map intact even when a month renders zero cubes. Months that lose contributions have their
previous `contrib_cube_MM` SCAD files (and any lingering STLs when `--gridfinity-cubes` is disabled)
removed automatically so the folder mirrors the current activity snapshot—even if a later run omits
the `--gridfinity-cubes` flag.
Yearly `stl/<year>/README.md` summaries add a **Gridfinity** section whenever these flags are used, listing
the generated layout and cube outputs so printable files are easy to locate. Cube entries always note
`SCAD + STL`, even when you omit `--stl`, because the CLI renders those meshes automatically. The layout entry notes
the detected footprint (for example `6×2 grid`) to confirm the chosen column count.

Open [docs/viewer.html](docs/viewer.html) in a browser to preview generated STL files with
[Three.js](https://threejs.org/) and experiment with different color counts.
Use the file picker to load your baseplate and `_colorN` (or legacy `levelN`)
STLs—the viewer automatically maps these names back to the color groups that the CLI
generates, shows a detected block-color count next to the picker, and rebuilds the Colors
dropdown so it shrinks or expands to the detected files, making manual selection optional.
Choose a lower value to hide higher-order color stacks while you inspect the layout; the
baseplate always remains visible so its footprint stays aligned. Even when you only load
later `_colorN` files, the dropdown still expands to the highest detected stack so those
meshes remain visible by default.

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
# the CI configuration. Import it via `from gitshelves import scad_to_stl` and
# ensure `xvfb-run` is installed on headless systems.
openscad -o stl/2024/baseplate_2x6.stl \
    --export-format binstl openscad/baseplate_2x6.scad
```

Run `black --check .`, `pytest -q`, and `codespell docs README.md` before submitting
changes. Add project-specific terms to `dict/allow.txt`.

### Render bundled OpenSCAD templates

Generate STL previews for the static templates bundled with the repository by
running:

```bash
python -m gitshelves.render.static --output-root stl/static
```

The helper skips vendored `openscad/lib/` directories, mirroring the CI job that
converts every packaged `.scad` file to a binary STL artifact. Override
`--source-root` when testing alternate template directories.

## Import migration helpers

The package layout now splits fetch/transform helpers under `gitshelves.core`
and rendering utilities under `gitshelves.render`. Use
`scripts/migrate_package_layout.py` to update downstream imports:

```bash
python scripts/migrate_package_layout.py path/to/file.py --write
```

The script performs string replacements for the legacy module names so
automation and local projects stay in sync with the refactor.

## STL Build Outputs

The `build-stl` workflow runs on every push and pull request targeting `main`
inside the `openscad/openscad:latest` container and attaches the rendered STL
files as downloadable artifacts. It installs `xvfb` with `apt` before invoking
`xvfb-run openscad` so container builds mirror local conversions. Navigate to
the workflow run and download `stl-<year>` to obtain the converted models.
To avoid bloating the repository, pre-generated baseplate models are no longer stored in the repo. Download the `stl-<year>` artifact or generate them locally.
Each `stl/<year>` directory includes a generated `README.md` summarizing the baseplate and monthly
cube counts. The README links to the bundled `baseplate_2x6.scad`, and when `--stl` is supplied the
CLI also renders `baseplate_2x6.stl` alongside the summary so the standard Gridfinity plate is ready
to print without extra commands. Re-running without `--stl` removes any lingering
`baseplate_2x6.stl` meshes so yearly folders only contain artifacts from the current run. The CLI writes these summaries and baseplates for every year in the
requested range, even when a year has no contributions, so your shelf layout stays predictable.
Day-level views are also written to `stl/<year>/<calendar-slug>/` as OpenSCAD files. Each
calendar mirrors the monthly grid width when `--calendar-days-per-row` is omitted, matching the
requested layout (`monthly-{months_per_row}x6`). Use `--calendar-days-per-row` to widen or narrow the
rows as needed; the CLI still adds a partial row for 31-day months. The folder slug mirrors the
configured width (for example `monthly-7x6` when
seven days share a row). Days without activity are annotated as reserved slots (for example
`// 2024-02-05 (0 contributions) reserved at [48, 0]`) so you can confirm spacing even when a
cube isn't generated.
Monthly `.scad` exports reserve slots for every month in the requested range as well, so years without
activity remain in place—they simply render zero-height stacks until you contribute again.
Months without contributions are annotated in the SCAD output so you can confirm each slot's
position when previewing or editing the file.
## Troubleshooting

OpenSCAD exits with status 1 when it cannot access an X display. The
`scad_to_stl` helper wraps the command in `xvfb-run` when `$DISPLAY` is
unset or empty. Install `xvfb-run` if you still encounter this error on a headless
machine.
