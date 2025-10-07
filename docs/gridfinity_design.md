# Gitshelves × Gridfinity – Design Specification
*(v0.9 – 2025-07-29)*

---

## 1  Background & Goal

`gitshelves` visualizes personal GitHub activity as physical objects.
This iteration makes the project **Gridfinity-compatible** so that the printed parts integrate with the de-facto 42 × 42 mm modular storage standard.
We want:

* **stl/** at repo root  
  * **2021 … 2025** sub-folders (five total).  
* Each folder holds one `baseplate_2x6.stl`, automatically generated from its matching `.scad`.

* **OpenSCAD sources** describing  
* A **2 × 6 base plate** (6 columns, 2 rows) that obeys the 42 mm grid and 41.5 mm clearance rules.
  * A **"contribution cube"** (1 × 1 × 1 U) used to encode the order of magnitude of monthly commits.

* **CI pipeline** (GitHub Actions) that converts every `*.scad` into a binary STL artifact on each
  push and publishes them as build outputs.

* Gridfinity libraries vendored (or declared as `git submodule`) so anyone can regenerate the models locally.

---

## 2  Gridfinity Primer (key spec excerpts)

| Parameter | Value | Source |
|-----------|-------|--------|
| Grid pitch (X/Y) | **42 mm** nominal; bins undersize to **41.5 mm** to give ±0.25 mm clearance | printables.com |
| Unit height (U)  | **7 mm** multiples | gridfinity.xyz |
| Corner magnet recess | Ø6 × 2 mm countersunk pockets recommended | r/Gridfinity / Thangs |
| Stack-locking lip | 0.35 mm interference recommended for secure stacking | r/Gridfinity |
| Base-plate tolerances | 0.5 mm cumulative shrink across rows → keep part-to-part tolerances independent | r/Gridfinity |

(See additional references in §9.)

---

## 3  Repository Layout

```
gitshelves/
├─ .github/workflows/
│  └― build-stl.yml # CI (see §5)
├─ openscad/ # All CAD sources live here
│  ├─ baseplate_2x6.scad
│  ├─ contrib_cube.scad
│  └― lib/gridfinity-rebuilt/ # git submodule
├─ stl/
│  ├─ 2021/baseplate_2x6.stl
│  ├─ …
│  └― 2025/baseplate_2x6.stl
└― docs/gridfinity_design.md # ← this file
```

---

## 4  OpenSCAD Implementation Details

### 4.1  Third-party library  
Use **kennetek/gridfinity-rebuilt-openscad** (MIT) as a submodule, providing canonical modules `gridfinityBaseplate()` and `bin()`. We also consult **vector76/gridfinity_openscad** (MIT) for additional design guidance.

```scad
// openscad/baseplate_2x6.scad
// Render with:  openscad -o ../stl/YYYY/baseplate_2x6.stl baseplate_2x6.scad

include <lib/gridfinity-rebuilt/gridfinity-rebuilt-baseplate.scad>;

// grid_x = columns, grid_y = rows
gridfinity_baseplate(grid_x = 6,
                     grid_y = 2,
                     u_height = 6,          // keep stock 6-U thickness
                     lip = true,            // stacking lip
                     magnet_style = "gridfinity_refine",
                     magnets_corners_only = false,
                     screw_holes = false);
```

### 4.2 Contribution cube
Each cube is a 1 × 1 × 1 U bin with a solid top; color is a post-print choice (filament swap).
Stacking one cube per order of magnitude (1s, 10s, 100s,…) produces a vertical bar chart for each month.

```scad
// openscad/contrib_cube.scad
use <lib/gridfinity-rebuilt/gridfinity-rebuilt-bin.scad>;

bin(
    ux = 1, uy = 1, uh = 1,              // 1×1 base, 1 unit high
    walls = 1.2, floor = 1.6, lid = "none",
    magnet_pockets = false,              // cubes don’t need magnets
    stackable = true                     // preserves Gridfinity lip
);
```

### 4.3 CLI-generated layouts
`gitshelves.cli` now exposes `--gridfinity-layouts`, producing
`stl/<year>/gridfinity_plate.scad` files that size a baseplate to the requested
column count (default six) and stack Gridfinity bins for each month on top of
it. Adjust `--gridfinity-columns` to generate other footprints without editing
OpenSCAD manually. Pair the flag with `--gridfinity-cubes` to emit
`contrib_cube_MM.scad`/`.stl` stacks so monthly prints are pre-scaled to each
month's contribution magnitude.

## 5  GitHub Actions Pipeline (.github/workflows/build-stl.yml)

| Step | Action |
|------|--------|
| checkout | actions/checkout@v4 |
| setup OpenSCAD | Use Docker image openscad/openscad:latest |
| build | install openscad and xvfb via apt; run `xvfb-run openscad` per file |
| matrix | Years = [2021…2025]; pass -Dyear=… if future parameterisation needed |
| artifacts | Upload rendered STLs; optionally commit stl/YYYY/ via github-push-action@v0.8.0. |

Example (high-level):

```yaml
name: build-stl

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  render:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        year: [2021, 2022, 2023, 2024, 2025]
    steps:
    - uses: actions/checkout@v4
      with:
        submodules: recursive
    - name: Install OpenSCAD + Xvfb
      run: |
        sudo apt-get update -qq
        sudo apt-get install -y --no-install-recommends openscad xvfb
    - name: Build STL
      run: |
        mkdir -p stl/${{ matrix.year }}
        xvfb-run --auto-servernum --server-args="-screen 0 1024x768x24" \
          openscad -o stl/${{ matrix.year }}/baseplate_2x6.stl \
            openscad/baseplate_2x6.scad --export-format binstl
```

The action internally calls

```
xvfb-run --auto-servernum --server-args="-screen 0 1024x768x24" \
  openscad -o stl/$year/baseplate_2x6.stl openscad/baseplate_2x6.scad --export-format binstl
```

---

## 6  Dependency Declaration
Gridfinity-Rebuilt-OpenSCAD (submodule at openscad/lib/gridfinity-rebuilt) – provides parametric geometry
OpenSCAD ≥ 2024.06 – required for FAST CSG and customizer options
CI installs OpenSCAD with `apt` and runs the CLI directly

The root README's *Dependencies* section now links to these libraries and highlights the
`xvfb-run` helper for headless renders so documentation stays aligned with automated tests.

## 7  Printing & Assembly Notes
PLA/PLA+ recommended for cubes; PETG for long 2×6 base (reduces warp).
For fridge/white-board mounting insert Ø6×2 mm N35 magnets into each corner pocket before final layer.

Colour scheme:

* Units (1–9) – light shade
* Tens – medium
* Hundreds – dark
* Thousands – neon / accent

This creates an intuitive heat-map effect.

## 8  Usage Guide & AMS automation
[docs/usage.md](usage.md) now captures the recommended slicer presets and AMS
filament-change scripts for multi-color prints. Refer contributors there for
printer tuning details and automation examples instead of treating the guidance
as future work.

## 9  Reference Sources
Base-plate tolerance discussion – Reddit
Bin clearance confirmation – Reddit
Official community spec summary – Printables
Magnet polarity guidelines – Reddit
Extended spec & stacking lip debate – Reddit
Parametric OpenSCAD libraries – GitHub
vector76/gridfinity_openscad – GitHub
Chris’s Notes
Gridfinity primer articles – All3DP
gridfinity.perplexinglabs.com
Thangs base-plate design tips – Thangs
OpenSCAD CLI manual – Wikibooks
Docker image for headless builds – GitHub
GitHub Action wrapper for OpenSCAD – GitHub

---

## Codex Prompt (paste verbatim)

> **System**: You are a senior DevOps & CAD automation engineer.  
> **User**:
> 1. Clone `https://github.com/futuroptimist/gitshelves`.
> 2. Add submodule `kennetek/gridfinity-rebuilt-openscad` at `openscad/lib/gridfinity-rebuilt`.
> 3. Review `vector76/gridfinity_openscad` for design guidance; do not vendor its sources.
> 4. Create `openscad/baseplate_2x6.scad` and `openscad/contrib_cube.scad` per the spec in `docs/gridfinity_design.md`.
> 5. Generate folders `stl/{2021..2025}` (keep empty – CI will fill).
> 6. Add `.github/workflows/build-stl.yml` implementing the matrix build using apt-installed OpenSCAD; output binary STLs.
> 7. Update root `README.md` to include a *Dependencies* and *How to Build Locally* section.
> 8. Commit, sign off (`git commit -s`), and open a pull-request titled “Gridfinity support & automated STL builds”.
> **Assistant**: implement every step and show the diff.
