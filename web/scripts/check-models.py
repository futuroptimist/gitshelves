import math, struct, sys

for name in sys.argv[1:]:
    data = open(name, "rb").read()
    assert len(data) > 84
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + 50 * count and count > 0
    values = []
    for i in range(count):
        values.extend(struct.unpack_from("<12fH", data, 84 + i * 50)[:12])
    assert all(math.isfinite(v) for v in values)
    coordinates = values[3:]
    assert max(coordinates) - min(coordinates) > 0
    print(f"{name}: {len(data)} bytes, {count} finite triangles")
