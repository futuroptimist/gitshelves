# Gitshelves Docs

The CLI can export OpenSCAD scripts and, if `openscad` is installed, STL meshes.
Use `--months-per-row` (a positive integer) to control the grid width, `--stl`
to specify an STL output path, and `--colors` to split blocks into up to four
color groups.
`docs/viewer.html` previews the resulting STLs in the browser with Three.js.

## Prompts

- [Repo feature summary prompt](repo_feature_summary_prompt.md) – collect flywheel feature data
- [Codex automation prompt](prompts-codex.md) – baseline instructions for automated agents.
- [Codex spellcheck prompt](prompts-codex-spellcheck.md) – fix typos in docs.
