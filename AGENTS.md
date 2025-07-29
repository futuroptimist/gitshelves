# Gitshelves Agent Guide

> Gitshelves generates 3D printable GitHub contribution charts from the GitHub API. Use this guide when updating code or docs.

## Project Structure
- `gitshelves/` Python package with CLI modules
- `tests/` pytest suite
- `docs/` additional documentation
- `.github/workflows/build-stl.yml` renders STL files from SCAD sources
- `openscad/lib/gridfinity-rebuilt/` placeholder for Gridfinity library (clone manually)

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
4. Clone the Gridfinity library into `openscad/lib/gridfinity-rebuilt` if it's missing.
