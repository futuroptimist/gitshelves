#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LIB="$ROOT/openscad/lib/gridfinity-rebuilt"
PIN="910e22d8607fd7f5f51ad5e5cbc5287a76810bfd"
if [[ ! -f "$LIB/gridfinity-rebuilt-baseplate.scad" ]]; then
  backup="$(mktemp -d)/gridfinity-rebuilt"
  mv "$LIB" "$backup"
  restore_library() { rm -rf "$LIB"; mv "$backup" "$LIB"; }
  trap restore_library EXIT
  git clone --filter=blob:none https://github.com/kennetek/gridfinity-rebuilt-openscad.git "$LIB"
  git -C "$LIB" checkout --detach "$PIN"
fi
command -v openscad >/dev/null || { echo "openscad is required to prepare models" >&2; exit 1; }
mkdir -p "$ROOT/web/public/models"
runner=(); [[ -n "${DISPLAY:-}" ]] || runner=(xvfb-run --auto-servernum)
"${runner[@]}" openscad -o "$ROOT/web/public/models/baseplate_2x6.stl" --export-format binstl "$ROOT/openscad/baseplate_2x6.scad"
"${runner[@]}" openscad -o "$ROOT/web/public/models/contrib_cube.stl" --export-format binstl "$ROOT/openscad/contrib_cube.scad"
test -s "$ROOT/web/public/models/baseplate_2x6.stl" && test -s "$ROOT/web/public/models/contrib_cube.stl"
python3 "$ROOT/web/scripts/validate-stl.py" "$ROOT/web/public/models/baseplate_2x6.stl" "$ROOT/web/public/models/contrib_cube.stl"
