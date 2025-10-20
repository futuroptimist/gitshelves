# Gitshelves Docs

For setup and usage details, see the [README](../README.md).

Authentication tokens resolve in the documented fallback order: an explicit
`--token` argument takes precedence, followed by the `GH_TOKEN` environment
variable and then `GITHUB_TOKEN`. The CLI and underlying fetch helpers share
this priority chain so local runs and CI jobs behave the same way.

The CLI can export OpenSCAD scripts and, if `openscad` is installed, STL meshes
using binary output (`--export-format binstl`) to mirror the CI workflow.
Use `--output` to change the `.scad` filename, `--months-per-row` to control the
grid width, `--stl` to specify an STL output path, and `--colors` to split
blocks into up to four color groups. Reruns without `--stl` delete any lingering
monthly STL so the output directory reflects the latest invocation, even when
previous metadata is missing. `--colors 2`
writes `*_color1.scad` and
`*_color2.scad`, `--colors 3` and `--colors 4` add the matching `*_color3.scad`
and `*_color4.scad`, and `--colors 5` keeps the same four block files while
funnelling extra logarithmic levels into the accent color. Smaller palettes
balance the logarithmic levels across the available groups while preserving
their chronological order, so `--colors 2`, `--colors 3`, and `--colors 4`
distribute stacks as evenly as possible before the accent color collects the
overflow.
Switching to multi-color runs removes any existing combined `<name>.scad`/`.stl`
output so the `_colorN` files fully replace the single-color export.

Every SCAD export is paired with JSON metadata that records the geometry flags,
resolved years, and output paths for the SCAD/STL pair. When no STL is
generated the file sets `"stl_generated"` to `false` and stores `null` in
`"stl"`, making STL omissions explicit for downstream tooling.
Gridfinity layout metadata includes the detected footprint by storing both the
column count and the calculated number of rows so scripts can reproduce plate
dimensions without scraping README summaries.
Even when intermediate logarithmic levels are absent, `_color4` still gathers the remaining high
orders so the accent file continues to highlight the peak contribution range.
`--months-per-row` values below one exit with a parser error before any files are
generated so invalid layouts never produce partial outputs. When you omit
`--calendar-days-per-row`, the CLI mirrors the monthly grid so daily calendars adopt
the same width (`monthly-12x6` by default). Provide `--calendar-days-per-row` to widen
or narrow the daily calendar rows without changing the monthly summary grid.
`--baseplate-template` selects which bundled Gridfinity baseplate (such as
`baseplate_1x12.scad`) is copied when multi-color exports request a baseplate.
`--gridfinity-layouts` writes `stl/<year>/gridfinity_plate.scad` so Gridfinity
bins are stacked onto a parametric baseplate; adjust the footprint with
`--gridfinity-columns`. Supply a positive integer—values below one raise a
parser error before any files are generated. When `--stl` is provided, the CLI also renders
`stl/<year>/gridfinity_plate.stl` so baseplates are printable without manual
conversion. Omitting `--stl` deletes any existing layout STLs so the folder
matches the current run, and skipping `--gridfinity-layouts` on a later run removes any
previous `gridfinity_plate.*` outputs so folders do not accumulate stale
layouts. Enable `--gridfinity-cubes` to export `contrib_cube_MM.scad` stacks for
every month with activity. Matching `contrib_cube_MM.stl` meshes are rendered
automatically whenever this flag is enabled—even without `--stl`—so install
`openscad` on systems that generate cube stacks. Months that no longer
record activity remove any existing `contrib_cube_MM` exports so only active
months keep cube stacks on disk. Runs that omit `--gridfinity-cubes` also clear
those cube files so directories always reflect the latest activity
snapshot. By default, the current year's contributions are fetched unless
`--start-year` and `--end-year` specify a range. Months that no longer have
contributions remove their old `contrib_cube_MM` files (and any lingering STLs
when cube meshes are not requested elsewhere) so directories stay in sync with the
latest activity snapshot.
Color-specific outputs also repeat the zero-contribution annotations so each
file documents the full monthly layout even when opened in isolation.
Whether no month produces any blocks or only some of the requested color groups
contain geometry, the CLI still writes `_colorN.scad` placeholders containing
those annotations so downstream automation continues to receive the expected
files; STL conversion is skipped for these empty color groups and any existing
`_colorN.stl` meshes are removed so unused slots do not leave stale geometry
behind.
When you dial the palette down, `_colorN.scad` files beyond the active range are
deleted alongside those `_colorN.stl` meshes (and every `_colorN.stl` is purged
when `--stl` is omitted), keeping the folder limited to the current color set.
Switching to multi-color exports removes the unified `<name>.scad` artifact and its
metadata so only the `_colorN` files remain in the output directory.
Switching back to single-color exports with `--colors 1` removes any lingering
`_colorN` SCAD/STL outputs so only the unified contribution file remains.

`load_baseplate_scad('baseplate_1x12.scad')` provides a bundled single-row Gridfinity plate when you need taller stacks without
cloning the OpenSCAD templates.

For printer-specific guidance, see the [usage guide](usage.md) with slicer
presets and AMS filament scripting examples.

Consult the [CLI output matrix](cli_matrix.md) for visual summaries of how
`--colors`, `--months-per-row`, and the `--gridfinity-*` flags combine to produce
specific SCAD/STL files.
The CLI always writes yearly summaries in `stl/<year>/README.md` for every year in the
requested range and copies the bundled `baseplate_2x6.scad` into each folder (rendering
`baseplate_2x6.stl` when `--stl` is provided) so folders exist even when a year has zero contributions.
Running the CLI without `--stl` clears any leftover `baseplate_2x6.stl` meshes so yearly
directories mirror the current run.
The README links to both artifacts, making it clear when an STL was generated for the baseplate.
When `--gridfinity-layouts` or `--gridfinity-cubes` are enabled, the summary gains a **Gridfinity**
section that lists the generated layout and cube outputs for quick reference. Cube entries explicitly
note `SCAD + STL`, even without `--stl`, because the CLI renders those meshes automatically. The layout entry also
records the detected footprint (for example `6×2 grid`) so you can confirm the selected column
count.
Monthly day-level calendars live in `stl/<year>/<calendar-slug>/`. Each SCAD arranges up to
five days per row and mirrors the monthly grid width when `--calendar-days-per-row` is omitted
so the footprint stays within a 256 mm square build area (`monthly-12x6` by default). Adjust the
width with `--calendar-days-per-row` when you need a different footprint; the directory slug
mirrors the configured width (for example `monthly-7x6` when seven days share a row). Days with no
activity add reserved-slot comments (for example `// 2024-02-05 (0 contributions) reserved at [48, 0]`)
so you can confirm spacing even when a cube is absent. Monthly contribution `.scad` exports reserve
every month in the requested range too, keeping the layout stable for years that currently have zero
contributions.
Zero-contribution months are annotated in the generated SCAD so you can double-check slot
positions even when no cubes are rendered.
[`viewer.html`](viewer.html) previews the resulting STLs in the browser with
[Three.js](https://threejs.org/). Load the baseplate and `_colorN` (or legacy
`levelN`) STLs to see each color group rendered with its own material. The viewer
automatically infers how many color groups are present from the filenames,
displays the detected block-color count next to the picker, and rebuilds the Colors
dropdown so it shrinks or expands to the detected total for quick confirmation.
Select a smaller count to temporarily hide higher-order color stacks while you review the
model; the baseplate stays visible so the footprint remains anchored. If you only import
later `_colorN` files, the dropdown still stretches to the highest detected stack so those
meshes remain visible without extra clicks.

## Prompts

- [Repo feature summary prompt](prompts/codex/repo-feature-summary.md) – collect flywheel feature data
- [Codex automation prompt](prompts/codex/automation.md) – baseline instructions for automated agents.
- [Codex spellcheck prompt](prompts/codex/spellcheck.md) – fix typos in docs.

## Design

- [Gridfinity design specification](gridfinity_design.md) – baseplate and cube dimensions.

## Spellcheck

Run `codespell` to catch typos. Project-specific words such as Gitshelves,
Gridfinity, OpenSCAD, and Xvfb live in `dict/allow.txt`. Keep the list sorted
alphabetically.
