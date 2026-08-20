#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-$ROOT/web/public/models}"
LIB="$ROOT/openscad/lib/gridfinity-rebuilt"
PIN=55fc273ddce8a5ea4c0575d6005482baa82951a7
if [[ ! -f "$LIB/gridfinity-rebuilt-baseplate.scad" ]]; then
  rm -rf "$LIB"; git clone -q https://github.com/kennetek/gridfinity-rebuilt-openscad.git "$LIB"; git -C "$LIB" checkout -q "$PIN"
fi
if [[ ! -e "$LIB/gridfinity-rebuilt-bin.scad" ]]; then ln -s gridfinity-rebuilt-bins.scad "$LIB/gridfinity-rebuilt-bin.scad"; fi
mkdir -p "$OUT"
command -v openscad >/dev/null || { echo "openscad is required to prepare exact models" >&2; exit 1; }
run=(openscad); [[ -n "${DISPLAY:-}" ]] || run=(xvfb-run --auto-servernum --server-args="-screen 0 1024x768x24" openscad)
"${run[@]}" -o "$OUT/baseplate_2x6.stl" "$ROOT/openscad/baseplate_2x6.scad" --export-format binstl
"${run[@]}" -o "$OUT/contrib_cube.stl" "$ROOT/openscad/contrib_cube.scad" --export-format binstl
python "$ROOT/web/scripts/check-models.py" "$OUT/baseplate_2x6.stl" "$OUT/contrib_cube.stl"
