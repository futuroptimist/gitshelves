# Gitshelves Agent Guide

> Gitshelves generates 3D printable GitHub contribution charts from the GitHub API. Use this guide when updating code or docs.

## Project Structure
- `gitshelves/` Python package with CLI modules
- `tests/` pytest suite
- `docs/` additional documentation
- `.github/workflows/build-stl.yml` removes any existing Gridfinity library folder, clones the library, installs OpenSCAD via `apt`, renders STL files from SCAD sources, and uploads them as workflow artifacts
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
