import { describe, expect, it } from "vitest";
import * as THREE from "three";
import { STLExporter } from "three/examples/jsm/exporters/STLExporter.js";
import { datasetFromCounts } from "../src/domain";
import { readStlFiles, type LocalStl } from "../src/files";
import { baseDisplayGeometry, exactInstancePlan } from "../src/scene";

function baseBytes(x = 0, y = 0, width = 256, depth = 88): Uint8Array {
  const geometry = new THREE.BoxGeometry(width, depth, 6);
  geometry.translate(x, y, 3);
  const material = new THREE.MeshBasicMaterial();
  const mesh = new THREE.Mesh(geometry, material);
  const bytes = new TextEncoder().encode(new STLExporter().parse(mesh));
  geometry.dispose();
  material.dispose();
  return bytes;
}

describe("canonical base display placement", () => {
  it("aligns the centered base with every existing module cell and the proxy", () => {
    const base: LocalStl = {
      name: "baseplate_2x6.stl",
      type: "base",
      colorGroup: 0,
      bytes: baseBytes(),
      canonicalBase: true,
    };
    const original = base.bytes.slice();
    const dataset = datasetFromCounts(Array(12).fill(10));
    for (const exploded of [false, true]) {
      const geometry = baseDisplayGeometry(base);
      const bounds = geometry.boundingBox!;
      expect(bounds.min.toArray()).toEqual([-2, -2, 0]);
      expect(bounds.max.toArray()).toEqual([254, 86, 6]);
      expect(bounds.getSize(new THREE.Vector3()).toArray()).toEqual([
        256, 88, 6,
      ]);
      expect(bounds.getCenter(new THREE.Vector3()).toArray()).toEqual([
        126, 42, 3,
      ]);
      const plan = exactInstancePlan(dataset, exploded);
      for (const [index, item] of plan.entries()) {
        const month = Math.floor(index / 2);
        expect(item.x).toBe(21 + (month % 6) * 42);
        expect(item.y).toBe(21 + Math.floor(month / 6) * 42);
        expect(item.z).toBe(
          6 + (index % 2) * (exploded ? 17 : 7) + (exploded ? 8 : 0),
        );
        for (const axis of ["x", "y"] as const) {
          expect(item[axis] - 20.75).toBeGreaterThan(bounds.min[axis]);
          expect(item[axis] + 20.75).toBeLessThan(bounds.max[axis]);
        }
      }
      geometry.dispose();
    }
    expect(base.bytes).toEqual(original);
  });

  it.each([
    [0, 0, 256, 88],
    [126, 42, 256, 88],
    [0, 0, 504, 42],
  ])(
    "preserves an imported base at %i, %i with size %i x %i",
    async (x, y, width, depth) => {
      const bytes = baseBytes(x, y, width, depth);
      const input = Object.assign(new Blob([bytes.slice().buffer]), {
        name: "baseplate_2x6.stl",
      }) as File;
      const [base] = await readStlFiles([input]);
      expect(base!.canonicalBase).toBeUndefined();
      const geometry = baseDisplayGeometry(base!);
      expect(geometry.boundingBox!.min.toArray()).toEqual([
        x - width / 2,
        y - depth / 2,
        0,
      ]);
      expect(geometry.boundingBox!.max.toArray()).toEqual([
        x + width / 2,
        y + depth / 2,
        6,
      ]);
      expect(base!.bytes).toEqual(bytes);
      geometry.dispose();
    },
  );
});
