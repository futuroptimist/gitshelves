# Gitshelves Agent Guide

> Gitshelves generates 3D printable GitHub contribution charts from the GitHub API. Use this guide when updating code or docs.

## Project Structure
- `gitshelves/` Python package with CLI modules
- `tests/` pytest suite
- `docs/` additional documentation and prompts
- `.github/workflows/build-stl.yml` runs on pushes and pull requests to `main`, removes any existing Gridfinity library folder, clones the library, executes inside the `openscad/openscad:latest` container, installs Xvfb via `apt`, renders `openscad/baseplate_2x6.scad` to `stl/<year>/baseplate_2x6.stl` using `xvfb-run`, and uploads them as workflow artifacts
- `scad_to_stl` wraps `openscad` in `xvfb-run` automatically when `$DISPLAY` is missing to mirror the CI workflow
- `openscad/lib/gridfinity-rebuilt/` holds the Gridfinity library (MIT). CI clones it automatically; clone it manually for local builds and keep the `LICENSE` file. We consult vector76/gridfinity_openscad for guidance
- `openscad/shelf.scad` and its pre-rendered `stl/shelf.stl` define a basic wall shelf with drywall mounting holes
- `--colors` controls multi-color output, grouping logarithmic levels into up to four block colors

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


## Web MVP and releases
- `web/` is an isolated strict-TypeScript Vite/Three.js app. Use `npm ci`, then `npm run format`, `npm run lint`, `npm run typecheck`, `npm test`, and `npm run test:browser`.
- Generate ignored canonical assets with `scripts/fetch_gridfinity.sh` followed by `python scripts/prepare_web_models.py`; never commit generated web STLs or build output.
- Proxy geometry is display-only. Python/OpenSCAD remain canonical, and exact downloads must retain source bytes.
- The container serves `/`, `/healthz`, and `/livez` as non-root on port 8080. Helm releases require an immutable `main-<shortsha>` image tag.
- Update `docs/product-design.md`, `docs/roadmap.md`, and `docs/releasing.md` when the web, physical, or release contract changes. Sugarkube/Cloudflare configuration remains outside this repository.
