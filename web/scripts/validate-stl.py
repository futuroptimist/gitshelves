#!/usr/bin/env python3
"""Reject empty/non-finite/degenerate binary STL build artifacts."""

import math
import struct
import sys
from pathlib import Path

for argument in sys.argv[1:]:
    path = Path(argument)
    data = path.read_bytes()
    if len(data) < 84:
        raise SystemExit(f"{path}: too small")
    triangles = struct.unpack_from("<I", data, 80)[0]
    if triangles < 1 or len(data) != 84 + triangles * 50:
        raise SystemExit(f"{path}: malformed binary STL")
    points = []
    for offset in range(84, len(data), 50):
        points.extend(struct.unpack_from("<9f", data, offset + 12))
    if not all(math.isfinite(value) for value in points):
        raise SystemExit(f"{path}: non-finite coordinate")
    spans = [max(points[axis::3]) - min(points[axis::3]) for axis in range(3)]
    if any(span <= 0 or span > 1000 for span in spans):
        raise SystemExit(f"{path}: implausible bounds {spans}")
    print(f"{path}: {triangles} triangles, bounds {spans}")
