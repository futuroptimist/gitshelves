# Gitshelves Docs

For setup and usage details, see the [README](../README.md).

The CLI can export OpenSCAD scripts and, if `openscad` is installed, STL meshes.
Use `--output` to change the `.scad` filename, `--months-per-row` to control the
grid width, `--stl` to specify an STL output path, and `--colors` to split
blocks into up to four color groups. By default, the current year's contributions
are fetched unless `--start-year` and `--end-year` specify a range. Multi-color
exports include a `_baseplate` companion generated from
[`openscad/baseplate_2x6.scad`](../openscad/baseplate_2x6.scad).
[`viewer.html`](viewer.html) previews the resulting STLs in the browser with
[Three.js](https://threejs.org/).

## Prompts

- [Repo feature summary prompt](prompts/codex/repo_feature_summary_prompt.md) – collect flywheel feature data
- [Codex automation prompt](prompts/codex/prompts-codex.md) – baseline instructions for automated agents.
- [Codex spellcheck prompt](prompts/codex/prompts-codex-spellcheck.md) – fix typos in docs.

## Design

- [Gridfinity design specification](gridfinity_design.md) – baseplate and cube dimensions.

## Spellcheck

Run `codespell` to catch typos. Project-specific words such as Gitshelves,
Gridfinity, OpenSCAD, and Xvfb live in `dict/allow.txt`. Keep the list sorted
alphabetically.
