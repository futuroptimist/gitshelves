# Usage Guide

This guide expands on the CLI help in the [README](../README.md) with print-ready defaults for
Gridfinity-compatible shelves. It highlights slicer settings that keep the contribution cubes crisp
and includes a sample AMS filament-change script so multi-color prints line up with the exported
`--colors` outputs.

## Slicer Presets

The presets below assume a 0.4 mm nozzle and PLA/PLA+. Adjust temperatures to match your filament
manufacturer. Both profiles stay within a 256 mm × 256 mm build volume.

| Part | Layer Height | Perimeters | Infill | Notes |
|------|--------------|------------|--------|-------|
| Baseplate 2×6 | 0.2 mm | 4 | 20% gyroid | Enable elephant foot compensation; add 5 mm brim |
| Contribution cubes | 0.16 mm | 3 | 15% grid | Disable supports; use monotonic top surfaces |

Recommended cooling settings:

- Fan 100% after layer 3 for both parts.
- Slow external perimeters to 25 mm/s to preserve the Gridfinity lip geometry.
- Enable "Detect Thin Walls" to avoid skipping the stacking lip detail.

For slicers that support custom G-code on print start, add the following snippet to level the bed and
log the selected `--colors` count to the printer display:

```gcode
; Gitshelves base profile
G28 ; home all axes
M117 Gitshelves print
M118 Printing Gitshelves model - colors: [colors]
```

Replace `[colors]` with the number passed to the CLI so the message matches the generated files.

## AMS Filament Scripts

When using a Bambu Lab AMS (or similar multi-material unit), schedule filament swaps after the base
plate finishes. The example below assumes two filament changes, producing three color groups (base +
levels 1-2 + levels 3+).

```gcode
; Triggered at start of layer 32 (after baseplate is complete)
M400 ; wait for moves to finish
M600 A ; swap to Color 2 for levels 1-2
M118 Swapped to Color 2 for lower levels

; Triggered at start of layer 48
M400
M600 B ; swap to Color 3 for high levels
M118 Swapped to Color 3 for high levels
```

Pair the change heights with the layer numbers reported by your slicer preview. For four colors,
insert an additional block before the second swap and update the file list emitted by
`--colors 4`.
