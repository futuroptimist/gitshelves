# Gitshelves Docs

For setup and usage details, see the [README](../README.md).

The CLI can export OpenSCAD scripts and, if `openscad` is installed, STL meshes
using binary output (`--export-format binstl`) to mirror the CI workflow.
Use `--output` to change the `.scad` filename, `--months-per-row` to control the
grid width, `--stl` to specify an STL output path, and `--colors` to split
blocks into up to four color groups (pass `--colors 5` to unlock all four). `--gridfinity-layouts` writes
`stl/<year>/gridfinity_plate.scad` so Gridfinity bins are stacked onto a
parametric baseplate; adjust the footprint with `--gridfinity-columns`. By
default, the current year's contributions are fetched unless `--start-year` and
`--end-year` specify a range.
The CLI always writes yearly summaries in `stl/<year>/README.md` for every year in the
requested range so folders exist even when a year has zero contributions.
Monthly day-level calendars live in `stl/<year>/monthly-5x6/`. Each SCAD arranges up to five days per
row (with a partial row for 31-day months) so the footprint fits within a 256 mm square build area.
[`viewer.html`](viewer.html) previews the resulting STLs in the browser with
[Three.js](https://threejs.org/). Load the baseplate and `_colorN` (or legacy
`levelN`) STLs to see each color group rendered with its own material.

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
