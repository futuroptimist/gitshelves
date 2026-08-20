import { describe, expect, it } from "vitest";
import { blocksForContributions, placement, sampleDataset } from "../src/model";
import { parseMetadata } from "../src/metadata";
import { classifyFilename, preserveFile, validateStl } from "../src/files";
import { createManifest } from "../src/manifest";
import { moduleTransform } from "../src/scene";
describe("contribution model", () => {
  it("uses canonical logarithmic boundaries", () =>
    expect(
      [0, 1, 9, 10, 99, 100, 999, 1000].map(blocksForContributions),
    ).toEqual([0, 1, 1, 2, 2, 3, 3, 4]));
  it("places twelve months deterministically", () =>
    expect(Array.from({ length: 12 }, (_, i) => placement(i + 1))).toEqual(
      Array.from({ length: 12 }, (_, i) => ({
        column: i % 6,
        row: Math.floor(i / 6),
        x: (i % 6) * 42,
        y: Math.floor(i / 6) * 42,
      })),
    ));
  it("explodes vertical stacks", () =>
    expect(moduleTransform(1, 2, "exploded").elements[14]).toBeGreaterThan(
      moduleTransform(1, 2, "assembled").elements[14],
    ));
});
describe("local bundles", () => {
  it("parses metadata and rejects malformed input", () => {
    expect(
      parseMetadata(
        JSON.stringify({
          monthly_contributions: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100],
        }),
      ).months[11]?.blocks,
    ).toBe(3);
    expect(() => parseMetadata("{")).toThrow("not valid JSON");
    expect(() => parseMetadata("{}")).toThrow("no monthly");
  });
  it("classifies compatibility names", () => {
    expect(classifyFilename("baseplate_2x6.stl").component).toBe("baseplate");
    expect(classifyFilename("chart_color3.stl").colorGroup).toBe(3);
    expect(classifyFilename("old_level5.stl").colorGroup).toBe(5);
  });
  it("preserves bytes and rejects malformed STL", () => {
    const source = new Uint8Array([1, 2, 3]).buffer;
    expect([...preserveFile("a.stl", source).bytes]).toEqual([1, 2, 3]);
    expect(() => validateStl(new Uint8Array(source))).toThrow("too small");
  });
});
it("creates exact quantities and placements", () => {
  const manifest = createManifest(sampleDataset());
  expect(manifest.totalCubeQuantity).toBe(
    sampleDataset().months.reduce((n, m) => n + m.blocks, 0),
  );
  expect(manifest.months).toHaveLength(12);
  expect(
    Object.values(manifest.quantitiesByColorGroup).reduce((a, b) => a + b, 0),
  ).toBe(manifest.totalCubeQuantity);
});
