# K-021: pinned Gridfinity integration and mesh measurements

## Scope

Inspected main `d3e5ec21f7c2d80399f7455c66b98d1e7a44e4a0` on 2026-10-11.
The focused correction resolves the Python generator's repository-root lookup,
uses the supported `src/core/bin.scad` API (`new_bin` / `bin_render`) instead
of the nonexistent singular `gridfinity-rebuilt-bin.scad` and `bin` module,
imports the hole-options function explicitly, and makes refined/regular magnet
options mutually exclusive. The generated solid 1U bin matches the existing
canonical contribution cube; dimensions and placement are unchanged. Empty
stacks now guard against OpenSCAD's descending `[0:-1]` range.

The STL workflow now uses the same Gridfinity-Rebuilt commit as Docker and
web model preparation: `910e22d8607fd7f5f51ad5e5cbc5287a76810bfd`.

## Exported measurements

Measured binary STL vertices after full rendering, not source-derived estimates.
Renderer: official OpenSCAD 2026.10.05, default tessellation/backend.
Existing portable archive SHA256:
`66162d948f0627e48ba82ac049e56dadc168c4b0d8078fda3aefccee6d8896ad`.
All corrected exports completed without OpenSCAD warnings or errors.

| Model | Minimum XYZ (mm) | Maximum XYZ (mm) | Span XYZ (mm) | Triangles |
| --- | --- | --- | --- | --- |
| Canonical static cube | -20.75, -20.75, 0 | 20.75, 20.75, 10.482533 | 41.5 × 41.5 × 10.482533 | 400 |
| Generated one-level cube | -20.75, -20.75, 0 | 20.75, 20.75, 10.482533 | 41.5 × 41.5 × 10.482533 | 400 |
| Complete static 2x6 baseplate plus border | -126, -42, 0 | 254, 86, 6 | 380 × 128 × 6 | 2698 |
| Generated 6-column assembly, all 12 months at one level | -126, -42, 0 | 230.75, 62.75, 16.482533 | 356.75 × 104.75 × 16.482533 | 7404 |

The static and generated single cubes were byte-identical in this run (SHA256
`a1da011e2576a9d9e6e961c0e31c28358d47f00601a9f2e5936de0199bf17f68`).
OpenSCAD 2021.01 independently exported the corrected static assembly at
380 × 128 × 6 mm (7076 triangles). Its generated cube measured
41.5 × 41.5 × 10.547409 mm; tessellation changes the lip extremum. The regression
suite compares cube/stack heights against the canonical cube exported by the
same renderer and checks the exact 7 mm stacking increment. The CI assembly
fixture uses one occupied month to bound legacy CGAL render cost; the full
twelve-month measurements above use the 2026 renderer.

Current main, rendered with the same pinned library and 2026 renderer, emitted
`Ignoring unknown function 'bundle_hole_options'` but produced the same oversized
static assembly. The earlier 256 × 88 × 6 mm border-only preflight result was
**not reproduced** in this setup. Neither exit status nor a nonempty STL alone
is adequate integration validation. The regression suite rejects warnings/errors,
checks generated cube sizes, stacking and empty stacks, and verifies that the
baseplate contains actual grid geometry rather than only a border.

## Separate placement proposal — not implemented

The library centers the baseplate at the origin. The border currently starts
at `[-2, -2]`, so the complete assembly exceeds the Bambu A1's 256 mm bed width.
A separate correction would start the border at
`[-grid_x * 42 / 2 - padding, -grid_y * 42 / 2 - padding]` (here `[-128, -44]`).
The intended resulting outer envelope is 256 × 88 mm; it must be re-exported
and measured after that separately approved change.

Generated bins currently start at `[0, 0]` and extend beyond the centered plate.
A separate placement correction would offset cell centers by
`[-(columns - 1) * 21, -(rows - 1) * 21]`, preserving the standard 42 mm pitch.
Vertical seating and the existing 6 mm assembly offset also need a fit audit;
the upstream baseplate reports 5 mm height. This PR does not change that offset,
scale parts, claim physical calibration, or authorize printing.

## Reproduce

Fetch the pinned dependency into `openscad/lib/gridfinity-rebuilt` and run:

```sh
GRIDFINITY_RENDER_TESTS=1 python -m pytest -q tests/test_gridfinity_integration.py
```

`OPENSCAD` selects an executable; on Windows select `openscad.com` rather than
the GUI executable. Headless Linux uses `xvfb-run`. The dedicated CI job runs
these real exports in addition to the normal unit suite, using the official
`openscad/openscad:dev` linux/amd64 image pinned at
`sha256:3cb3f6347bdb64736d1bba690cffc2a33c8e3fd28780304fe5637569cade9853`.
The installed Windows 2021.01 renderer crashed on the canonical bin and timed
out on the twelve-bin union; it is not supported for these bin regressions. No STL artifacts are
committed. Physical calibration remains outstanding in [the roadmap](roadmap.md#2-physical-calibration).
