# Usage Guide

This guide expands on the README with slicer recommendations and automated
filament-change scripts so multi-color Gitshelves prints stay reproducible.

## Slicer presets

The contribution charts print as two distinct part families: thin-walled
baseplates and taller contribution cubes. Start with the presets below and
adjust for your printer's tolerances.

### Baseplate (2×6 Gridfinity)

- **Material**: PETG or ABS to minimize warp on the long span
- **Nozzle / layer height**: 0.4 mm nozzle at 0.24 mm layers
- **Perimeters**: 4 walls to reinforce the magnet lip
- **Top / bottom**: 5 solid layers; enable ironing for a flat top surface
- **Infill**: 20% gyroid balances rigidity with print time
- **Supports**: Off (all geometry is self-supporting)
- **Bed prep**: Glue stick or textured PEI sheet to avoid corner lift

### Contribution cubes

- **Material**: PLA or PLA+ for crisp edges and easy color swaps
- **Nozzle / layer height**: 0.4 mm nozzle at 0.20 mm layers
- **Perimeters**: 2 walls; cubes are solid after color swaps
- **Top / bottom**: 4 top and bottom layers
- **Infill**: 15% grid keeps cubes light without sacrificing strength
- **Supports**: Off
- **Filament change**: Enable color pause at the desired logarithmic level

## AMS filament scripts

Automated material handling keeps multi-color runs aligned across dozens of
cubes. The snippets below target common AMS workflows; treat them as templates
and adapt values to your equipment.

### Bambu Studio (AMS)

Add the following to *Settings → Filament → Filament Change G-code* so the
toolhead parks safely before the AMS swaps spools:

```gcode
; Pause for manual inspection before AMS change
M400                 ; finish buffered moves
G91                  ; relative positioning
G1 Z10 F1200         ; lift nozzle 10 mm
G90                  ; absolute positioning
G1 X0 Y220 F6000     ; park at the front-left
M400
M25                  ; Bambu pause (resumes automatically after swap)
```

### PrusaSlicer (M600-based pause)

For printers that rely on classic filament-change commands, create a custom
g-code macro and reference it via a color change marker:

```gcode
; Trigger filament swap at color transition
M400                 ; wait for moves to finish
G91
G1 Z8 F1200          ; raise nozzle to avoid scars
G90
G1 X20 Y200 F6000    ; park near the bed edge
M400
M600                 ; prompt operator for new filament
```

Include this macro under *Printer Settings → Custom G-code → Color Change* so
PrusaSlicer inserts it whenever you add a color transition marker.
