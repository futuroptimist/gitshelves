import { describe, expect, it } from "vitest";
import { cubesForContributions, placement } from "../src/contributions";
import {
  SAMPLE_DATASET,
  datasetFromCounts,
  parseMetadataText,
} from "../src/metadata";
import { classifyFilename, downloadBytes, isPlausibleStl } from "../src/files";
import { cubeTransform, groupVisible, reducedMotion } from "../src/transforms";
import { createManifest } from "../src/manifest";

describe("contribution model", () => {
  it.each([
    [0, 0],
    [1, 1],
    [9, 1],
    [10, 2],
    [99, 2],
    [100, 3],
    [999, 3],
    [1000, 4],
  ])("maps %i to %i", (count, height) =>
    expect(cubesForContributions(count)).toBe(height),
  );
  it("places twelve months deterministically", () =>
    expect(Array.from({ length: 12 }, (_, i) => placement(i + 1))).toEqual(
      Array.from({ length: 12 }, (_, i) => ({
        month: i + 1,
        column: i % 6,
        row: Math.floor(i / 6),
        x: (i % 6) * 42,
        y: Math.floor(i / 6) * 42,
      })),
    ));
  it("has boundary sample", () =>
    expect(
      SAMPLE_DATASET.months.map((x) => x.contributions).slice(0, 8),
    ).toEqual([0, 1, 9, 10, 99, 100, 999, 1000]));
});
describe("metadata", () => {
  it("parses metadata", () => {
    const monthly = Object.fromEntries(
      Array.from({ length: 12 }, (_, i) => [
        `2025-${String(i + 1).padStart(2, "0")}`,
        i,
      ]),
    );
    expect(
      parseMetadataText(
        JSON.stringify({ username: "octo", monthly_contributions: monthly }),
      ).months,
    ).toHaveLength(12);
  });
  it("parses run summary", () =>
    expect(
      parseMetadataText(
        JSON.stringify({ files: [{ monthly: Array(12).fill(1) }] }),
      ).source,
    ).toBe("run-summary"));
  it.each([
    "",
    "{",
    JSON.stringify({ nope: true }),
    JSON.stringify({ monthly: [-1, ...Array(11).fill(0)] }),
  ])("rejects invalid input", (text) =>
    expect(() => parseMetadataText(text)).toThrow(),
  );
});
describe("STLs", () => {
  it.each([
    ["x_baseplate.stl", "baseplate", null],
    ["x_color3.stl", "contribution", 3],
    ["level2.stl", "contribution", 2],
    ["contrib_cube.stl", "cube", 1],
  ])("classifies %s", (name, type, color) =>
    expect(classifyFilename(name as string)).toEqual({
      type,
      colorGroup: color,
    }),
  );
  it("preserves exact bytes", () => {
    const source = {
      name: "x.stl",
      type: "unknown" as const,
      colorGroup: null,
      size: 3,
      bytes: new Uint8Array([0, 255, 3]),
    };
    expect(downloadBytes(source)).toEqual(source.bytes);
    expect(downloadBytes(source)).not.toBe(source.bytes);
  });
  it("rejects malformed binary STL", () =>
    expect(isPlausibleStl(new Uint8Array(84))).toBe(false));
});
it("computes transforms", () => {
  const month = SAMPLE_DATASET.months[1]!;
  expect(cubeTransform(month, 1, "assembled").z).toBe(14);
  expect(cubeTransform(month, 1, "exploded").z).toBeGreaterThan(14);
});
it("supports palette and reduced motion", () => {
  expect(groupVisible(2, new Set([2]))).toBe(true);
  expect(reducedMotion({ matches: true } as MediaQueryList)).toBe(true);
});
it("builds manifest quantities and placements", () => {
  const manifest = createManifest(
    datasetFromCounts([0, 1, 9, 10, 99, 100, 999, 1000, 0, 0, 0, 0]),
    false,
  );
  expect(manifest.totalCubes).toBe(16);
  expect(manifest.placements).toHaveLength(12);
  expect(manifest.files.base).toBeNull();
});
