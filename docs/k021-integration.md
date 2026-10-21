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
same renderer, compares the complete normalized triangle signature for a single
cube (including internal geometry), and checks the exact 7 mm stacking increment. The CI assembly
fixture uses one occupied month to bound legacy CGAL render cost; the full
twelve-month measurements above use the 2026 renderer.

Current main, rendered with the same pinned library and 2026 renderer, emitted
`Ignoring unknown function 'bundle_hole_options'` but produced the same oversized
static assembly. The earlier 256 × 88 × 6 mm border-only preflight result was
**not reproduced** in this setup. Neither exit status nor a nonempty STL alone
is adequate integration validation. The regression suite rejects warnings/errors,
checks generated cube sizes, stacking and empty stacks, and verifies that the
baseplate contains actual grid geometry rather than only a border.

## Horizontal placement correction — 2026-10-21

The separately approved XY-only correction starts the static and packaged
border at `[-grid_x * 42 / 2 - padding, -grid_y * 42 / 2 - padding]`
(here `[-128, -44]`), matching the centered upstream plate. Generated bin
centers now include `[-(columns - 1) * 21, -(rows - 1) * 21]`.
Zero-contribution annotations use the same centered coordinates. The 42 mm
pitch, 7 mm stacking increment, 2 mm border padding, bin geometry and all
vertical dimensions are unchanged. The standalone cube and 1×12 template
are unchanged; generated layouts do not acquire the static border ring.

These are fresh binary-STL measurements, not calculated target bounds:

| Model | Minimum XYZ (mm) | Maximum XYZ (mm) | Span XYZ (mm) | Triangles |
| --- | --- | --- | --- | --- |
| Corrected static 2×6 baseplate plus border | -128, -44, 0 | 128, 44, 6 | 256 × 88 × 6 | 2652 |
| Corrected packaged 2×6 baseplate plus border | -128, -44, 0 | 128, 44, 6 | 256 × 88 × 6 | 2652 |
| Generated 6-column assembly, all 12 months at one level | -126, -42, 0 | 126, 42, 16.482533 | 252 × 84 × 16.482533 | 7404 |
| Generated 6-column empty plate | -126, -42, 0 | 126, 42, 5 | 252 × 84 × 5 | 2604 |
| Generated 5-column assembly, months 1 and 12 at one level | -105, -63, 0 | 105, 63, 16.482533 | 210 × 126 × 16.482533 | 4016 |

The before/after comparison used main
`c6eb8552b508500e865d8a402735cf6d7180b618` and the same pinned library and
renderer. Before correction, the full static baseplate-plus-border still
measured 380 × 128 × 6 mm, and the generated full assembly measured
356.75 × 104.75 × 16.482533 mm. The historical measurements above remain
valid for that old placement, not the corrected models.

Renderer: official Linux x86-64 OpenSCAD 2026.10.05 AppImage, default Manifold
backend, SHA256
`388c33da0848e54ec0b46b8e1e4ed05d83bd79865188db9ceba5ea5efdf619f3`.
Its checksum matched the official download. This run used Qt's offscreen
platform without Xvfb or a display server. The static and packaged corrected
plates were byte-identical, SHA256
`7e4445a2b175fd51f51f0eaac33ef435c9c65ca073ca12f53e000e9afb293f11`.
The canonical/generated single-cube hash remained
`a1da011e2576a9d9e6e961c0e31c28358d47f00601a9f2e5936de0199bf17f68`.

The real-render suite rejects warnings/errors, checks exact centered extrema,
and requires interior plate geometry in every cell so a correctly sized hollow
border cannot pass. First/last-month, full, empty and non-divisor-column layouts
are rendered; unit tests also cover odd/even and single-row/column layouts.
Canonical triangle matching and same-renderer cube/stack height checks remain.

**This is not print-ready or physical-fit acceptance.** The 256 mm static width
still has zero spare width on a 256 mm bed. The unchanged 6 mm bin offset sits
above a 5 mm plate and still needs a separate seating/fit audit. Neither the
new measurements nor a green regression suite authorizes printing or proves
that physical parts mate correctly.

## Reproduce

Fetch the pinned dependency into `openscad/lib/gridfinity-rebuilt` and run:

```sh
GRIDFINITY_RENDER_TESTS=1 python -m pytest -q tests/test_gridfinity_integration.py
```

`OPENSCAD` selects an executable; on Windows select `openscad.com` rather than
the GUI executable. Headless Linux uses `xvfb-run` by default. With a compatible
development renderer, setting `QT_QPA_PLATFORM=offscreen` instead selects the
verified non-GUI export route without Xvfb. The dedicated CI job runs
these real exports in addition to the normal unit suite, using the official
`openscad/openscad:dev` linux/amd64 image pinned at
`sha256:3cb3f6347bdb64736d1bba690cffc2a33c8e3fd28780304fe5637569cade9853`.
The installed Windows 2021.01 renderer crashed on the canonical bin and timed
out on the twelve-bin union; it is not supported for these bin regressions. No STL artifacts are
committed. Physical calibration remains outstanding in [the roadmap](roadmap.md#2-physical-calibration).
