import { describe, expect, it } from "vitest";
import {
  blocksForContributions,
  datasetFromCounts,
  SAMPLE,
} from "../src/domain";
import { classifyFilename } from "../src/files";
import { createManifest } from "../src/manifest";
import { moduleTransform, paletteVisible } from "../src/transforms";
import { parseMetadata } from "../src/metadata";
describe("product domain", () => {
  it.each([
    [0, 0],
    [1, 1],
    [9, 1],
    [10, 2],
    [99, 2],
    [100, 3],
    [999, 3],
    [1000, 4],
  ])("maps %i to %i cubes", (count, blocks) =>
    expect(blocksForContributions(count)).toBe(blocks),
  );
  it("places twelve months deterministically", () =>
    expect(SAMPLE.months.map((m) => [m.x, m.y])).toEqual([
      [0, 0],
      [42, 0],
      [84, 0],
      [126, 0],
      [168, 0],
      [210, 0],
      [0, 42],
      [42, 42],
      [84, 42],
      [126, 42],
      [168, 42],
      [210, 42],
    ]));
  it("computes assembled and exploded transforms", () => {
    expect(moduleTransform(SAMPLE.months[1]!, 1, false).z).toBe(13);
    expect(moduleTransform(SAMPLE.months[1]!, 1, true).z).toBe(31);
  });
  it("applies palette visibility", () => {
    expect(paletteVisible(0, new Set())).toBe(true);
    expect(paletteVisible(2, new Set([1]))).toBe(false);
  });
});
describe("imports", () => {
  it.each([
    ["x_baseplate.stl", "base", 0],
    ["x_color3.stl", "contribution", 3],
    ["x_level5.stl", "contribution", 5],
    ["contrib_cube.stl", "module", 0],
  ])("classifies %s", (name, type, group) =>
    expect(classifyFilename(name)).toMatchObject({ type, colorGroup: group }),
  );
  it("parses native web metadata", () =>
    expect(
      parseMetadata(
        JSON.stringify({
          schemaVersion: "gitshelves.web/v1",
          year: 2024,
          months: Array.from({ length: 12 }, (_, i) => ({ contributions: i })),
        }),
      ).months[11]?.contributions,
    ).toBe(11));
  it("parses current CLI metadata and run summaries", () => {
    const monthly = Array.from({ length: 12 }, (_, index) => ({
      year: 2024,
      month: index + 1,
      count: index * 10,
      blocks: 1,
    }));
    expect(
      parseMetadata(JSON.stringify({ monthly_contributions: monthly }))
        .months[11]?.contributions,
    ).toBe(110);
    expect(
      parseMetadata(
        JSON.stringify({ outputs: [{ monthly_contributions: monthly }] }),
      ).year,
    ).toBe(2024);
  });
  it.each(["", "nope", "[]", "{}"])(
    "rejects malformed/unsupported input",
    (text) => expect(() => parseMetadata(text)).toThrow(),
  );
});
it("creates quantities and placements", () => {
  const dataset = datasetFromCounts([1, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
  const manifest = createManifest(dataset);
  expect(manifest.totalCubeQuantity).toBe(3);
  expect(manifest.quantitiesByColorGroup).toEqual({ "1": 2, "2": 1 });
  expect(manifest.monthPlacements).toHaveLength(12);
});
