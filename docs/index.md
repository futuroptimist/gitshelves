# Gitshelves Docs

For setup and usage details, see the [README](../README.md).

The CLI can export OpenSCAD scripts and, if `openscad` is installed, STL meshes
using binary output (`--export-format binstl`) to mirror the CI workflow.
Use `--output` to change the `.scad` filename, `--months-per-row` to control the
grid width, `--stl` to specify an STL output path, and `--colors` to split
blocks into up to four color groups (pass `--colors 5` to unlock all four;
additional orders of magnitude share the fourth color).
`--months-per-row` values below one exit with a parser error before any files are
generated so invalid layouts never produce partial outputs.
`--baseplate-template` selects which bundled Gridfinity baseplate (such as
`baseplate_1x12.scad`) is copied when multi-color exports request a baseplate.
`--gridfinity-layouts` writes `stl/<year>/gridfinity_plate.scad` so Gridfinity
bins are stacked onto a parametric baseplate; adjust the footprint with
`--gridfinity-columns`. Supply a positive integer—values below one raise a
parser error before any files are generated. When `--stl` is provided, the CLI also renders
`stl/<year>/gridfinity_plate.stl` so baseplates are printable without manual
conversion. Enable `--gridfinity-cubes` to export `contrib_cube_MM.scad` stacks
for every month with activity, and pass `--stl` to render matching `.stl`
files. By default, the current year's contributions are fetched unless
`--start-year` and `--end-year` specify a range.
Color-specific outputs also repeat the zero-contribution annotations so each
file documents the full monthly layout even when opened in isolation.
When no month produces any blocks, the CLI still writes `_colorN.scad`
placeholders containing those annotations so downstream automation continues to
receive the expected files; STL conversion is skipped for these empty color
groups.

`load_baseplate_scad('baseplate_1x12.scad')` provides a bundled single-row Gridfinity plate when you need taller stacks without
cloning the OpenSCAD templates.

For printer-specific guidance, see the [usage guide](usage.md) with slicer
presets and AMS filament scripting examples.
The CLI always writes yearly summaries in `stl/<year>/README.md` for every year in the
requested range and copies the bundled `baseplate_2x6.scad` into each folder (rendering
`baseplate_2x6.stl` when `--stl` is provided) so folders exist even when a year has zero contributions.
When `--gridfinity-layouts` or `--gridfinity-cubes` are enabled, the summary gains a **Gridfinity**
section that lists the generated layout and cube outputs for quick reference. The layout entry also
records the detected footprint (for example `6×2 grid`) so you can confirm the selected column
count.
Monthly day-level
calendars live in `stl/<year>/monthly-5x6/`. Each SCAD arranges up to five days per row (with a
partial row for 31-day months) so the footprint fits within a 256 mm square build area. Days with no
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
model; the baseplate stays visible so the footprint remains anchored.

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
