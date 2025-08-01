# Gitshelves Agent Guide

> Gitshelves generates 3D printable GitHub contribution charts from the GitHub API. Use this guide when updating code or docs.

## Project Structure
- `gitshelves/` Python package with CLI modules
- `tests/` pytest suite
- `docs/` additional documentation
- `.github/workflows/build-stl.yml` removes any existing Gridfinity library folder, clones the library, installs OpenSCAD and Xvfb via `apt`, renders STL files from SCAD sources using `xvfb-run`, and uploads them as workflow artifacts
- `openscad/lib/gridfinity-rebuilt/` holds the Gridfinity library. CI clones it automatically; clone it manually for local builds

## Coding Conventions
- Python code is formatted with `black`
- Keep functions small with descriptive names
- Document non-obvious logic

## Testing Requirements
```bash
pip install -e .
pytest -q
```

## Pull Request Guidelines
1. Run all checks before pushing:
   ```bash
   black --check .
   pytest -q
   ```
2. Update `README.md` and `AGENTS.md` when CLI options or workflows change.
3. Include a clear description and reference relevant issues.
4. For local testing, clone `gridfinity-rebuilt-openscad` into `openscad/lib/gridfinity-rebuilt` if it's not already present.

## Gridfinity
The STL workflow uses Gridfinity base plates and contribution cubes. Month-to-cube height conversion follows the **Gridfinity scoring metric**:

- 1–9 contributions → 1 cube
- 10–99 contributions → 2 cubes
- 100–999 contributions → 3 cubes
- and so on

Mathematically `floor(log10(count)) + 1` cubes are stacked for any count ≥ 1 (else 0). This mirrors `gitshelves.scad.blocks_for_contributions()`.

