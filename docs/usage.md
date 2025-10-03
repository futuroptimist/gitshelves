# Usage Guide

This guide covers slicer presets and multi-color workflow tips for Gitshelves parts.
Start with the CLI instructions in the [README](../README.md) to generate `.scad`
and `.stl` files.

## Slicer Presets

The baseplate and contribution cubes benefit from different slicer settings.
Use the presets below as a starting point and adjust for your printer or material.

### Baseplate (`*_baseplate`)
- **Material:** PETG
- **Layer height:** 0.20 mm
- **Infill:** 20% gyroid
- **Supports:** Off
- **Notes:** Slow the first layer and add a 5 mm brim on smooth build plates to resist warping.

### Contribution cubes (`*_colorN`)
- **Material:** PLA or PLA+
- **Layer height:** 0.16 mm with adaptive steps for curved tops
- **Infill:** 15% rectilinear
- **Supports:** Off
- **Notes:** Enable ironing on the top layer for crisp block faces.

### Daily calendars (`monthly-5x6/*.scad`)
- **Material:** PLA
- **Layer height:** 0.20 mm
- **Infill:** 15%
- **Supports:** Off
- **Notes:** Arrange four calendars per plate or enable sequential printing to reduce travel moves.

Additional slicer suggestions:

- Increase first-layer line width to 120% on baseplates to improve adhesion.
- Disable the part cooling fan for the first five PETG layers to strengthen the bond.
- Group cubes by color in the build volume so AMS swaps stay predictable.

## AMS Filament Scripts

Multi-color prints produced with `--colors > 1` can take advantage of automatic
filament changers. The example below targets Bambu Studio, but the pattern can
be adapted to other slicers with AMS support.

```gcode
; Trigger a color swap before each block group
; Bambu Lab firmware honours the filament ID in the comment
M960 S0 ; ensure AMS is enabled
G92 E0  ; reset extruder
; --- Color 1 (baseplate) ---
;filament_type: PETG
;filament_colour: Base Grey
M400
; --- Color 2 (blocks level 1) ---
;filament_type: PLA
;filament_colour: Light Blue
M960 S1
M400
; --- Color 3 (blocks level 2+) ---
;filament_type: PLA
;filament_colour: Dark Blue
M960 S2
```

Tips for AMS jobs:

- Slice the baseplate separately when you want a different material or nozzle.
- Use `--colors 3` or `--colors 4` to keep higher contribution magnitudes on
  distinct filaments.
- Purge volumes can grow quickly; enable waste tower reuse when available.
- Export separate G-code files for baseplates and block groups to minimize
  idle time between color swaps.

## Troubleshooting

- If PETG baseplates curl, increase enclosure temperature or add a glue stick
  layer on the build plate.
- For cubes with visible Z seams, rotate the part 45° so seams hide on a corner.
- When printing daily calendars, enable sequential printing with a safe Z hop
  to prevent nozzle collisions.
