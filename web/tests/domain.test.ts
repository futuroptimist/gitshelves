import { describe, expect, it } from "vitest";
import {
  blocksForContributions,
  datasetFromCounts,
  SAMPLE,
} from "../src/domain";
import {
  appendLiteralFilename,
  classifyFilename,
  parseStlGeometry,
  readStlFiles,
} from "../src/files";
import { createManifest } from "../src/manifest";
import { moduleTransform, paletteVisible } from "../src/transforms";
import { parseMetadata } from "../src/metadata";
import { analyzeBundle, exactInstancePlan } from "../src/scene";
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
      blocks: index === 0 ? 0 : Math.floor(Math.log10(index * 10)) + 1,
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
  it("selects the latest year across all run-summary outputs", () => {
    const records = (year: number) =>
      Array.from({ length: 12 }, (_, index) => ({
        year,
        month: index + 1,
        count: year + index,
        blocks: Math.floor(Math.log10(year + index)) + 1,
      }));
    const dataset = parseMetadata(
      JSON.stringify({
        outputs: [
          { monthly_contributions: records(2023) },
          { monthly_contributions: records(2025) },
        ],
      }),
    );
    expect(dataset.year).toBe(2025);
    expect(dataset.months[0]?.contributions).toBe(2025);
  });
  it("rejects conflicting, inconsistent, and partial run summaries", () => {
    const complete = Array.from({ length: 12 }, (_, index) => ({
      year: 2025,
      month: index + 1,
      count: index,
      blocks: index === 0 ? 0 : Math.floor(Math.log10(index)) + 1,
    }));
    expect(() =>
      parseMetadata(
        JSON.stringify({
          outputs: [{ monthly_contributions: complete.slice(0, 11) }],
        }),
      ),
    ).toThrow("complete");
    expect(() =>
      parseMetadata(
        JSON.stringify({
          outputs: [
            { monthly_contributions: complete },
            {
              monthly_contributions: [{ ...complete[0], count: 2, blocks: 1 }],
            },
          ],
        }),
      ),
    ).toThrow("Conflicting");
    expect(() =>
      parseMetadata(
        JSON.stringify({
          monthly_contributions: [{ ...complete[1], blocks: 4 }],
        }),
      ),
    ).toThrow("Inconsistent");
  });
  it("accepts complete object metadata without inventing omitted months", () => {
    const complete = Object.fromEntries(
      Array.from({ length: 12 }, (_, index) => [String(index + 1), index]),
    );
    expect(
      parseMetadata(
        JSON.stringify({ year: 2025, monthly_contributions: complete }),
      ).year,
    ).toBe(2025);
    const yearMonth = Object.fromEntries(
      Array.from({ length: 12 }, (_, index) => [`2026-${index + 1}`, index]),
    );
    expect(
      parseMetadata(JSON.stringify({ monthly_contributions: yearMonth })).year,
    ).toBe(2026);
    expect(() =>
      parseMetadata(
        JSON.stringify({
          year: 2025,
          monthly_contributions: { ...complete, "12": undefined },
        }),
      ),
    ).toThrow("complete");
  });
  it.each([
    [{ year: 2025, monthly_contributions: { nope: 1 } }, "Invalid"],
    [
      {
        year: 2025,
        monthly_contributions: {
          ...Object.fromEntries(
            Array.from({ length: 12 }, (_, i) => [i + 1, i]),
          ),
          "12": -1,
        },
      },
      "Invalid",
    ],
    [{ monthly_contributions: { "2025-1": 1, "2026-2": 2 } }, "multiple years"],
  ])("rejects invalid or ambiguous object metadata", (value, error) =>
    expect(() => parseMetadata(JSON.stringify(value))).toThrow(error),
  );
  it.each(["", "nope", "[]", "{}"])(
    "rejects malformed/unsupported input",
    (text) => expect(() => parseMetadata(text)).toThrow(),
  );
});
function binaryTriangle(): Uint8Array {
  const bytes = new Uint8Array(134),
    view = new DataView(bytes.buffer);
  view.setUint32(80, 1, true);
  [
    [0, 0, 0],
    [1, 0, 0],
    [0, 1, 0],
  ].forEach((point, vertex) =>
    point.forEach((value, axis) =>
      view.setFloat32(84 + 12 + vertex * 12 + axis * 4, value, true),
    ),
  );
  return bytes;
}
it("keeps hostile filenames literal and preserves downloadable bytes", async () => {
  const prior = globalThis.document;
  const children: Array<{ textContent: string }> = [];
  Object.assign(globalThis, {
    document: { createElement: () => ({ textContent: "" }) },
  });
  const name = "<img src=x onerror=alert(1)>.stl";
  appendLiteralFilename(
    {
      append: (item: { textContent: string }) => children.push(item),
    } as unknown as HTMLElement,
    name,
  );
  expect(children).toEqual([{ textContent: name }]);
  const bytes = binaryTriangle();
  const input = Object.assign(new Blob([bytes.slice().buffer]), {
    name,
  }) as File;
  expect((await readStlFiles([input]))[0]?.bytes).toEqual(bytes);
  Object.assign(globalThis, { document: prior });
});
it("rejects empty, malformed, non-finite, and parse-failing STL geometry", () => {
  expect(() => parseStlGeometry(new Uint8Array(84))).toThrow();
  const malformed = binaryTriangle().slice(0, 100);
  expect(() => parseStlGeometry(malformed)).toThrow();
  const nonfinite = binaryTriangle();
  new DataView(nonfinite.buffer).setFloat32(96, Infinity, true);
  expect(() => parseStlGeometry(nonfinite)).toThrow("non-finite");
  expect(() =>
    parseStlGeometry(
      new TextEncoder().encode("solid facet normal vertex endfacet"),
    ),
  ).toThrow();
});
it("plans canonical 2x6 instances with mode transforms and color visibility", () => {
  const dataset = datasetFromCounts(Array(12).fill(10));
  const assembled = exactInstancePlan(dataset, false);
  const exploded = exactInstancePlan(dataset, true, new Set([1]));
  expect(new Set(assembled.map(({ x, y }) => `${x},${y}`)).size).toBe(12);
  expect(assembled).toHaveLength(24);
  expect(exploded[1]?.z).not.toBe(assembled[1]?.z);
  expect(exploded.filter((item) => !item.visible)).toHaveLength(12);
});
const local = (
  type: "base" | "module" | "contribution" | "unknown",
  colorGroup = 0,
) => ({ name: `${type}.stl`, type, colorGroup, bytes: new Uint8Array() });
it("analyzes exact and proxy bundle coverage without duplication", () => {
  const dataset = datasetFromCounts(Array(12).fill(100));
  for (const bundle of [
    [],
    [local("base")],
    [local("module")],
    [local("unknown")],
  ])
    expect(analyzeBundle(dataset, bundle).exact).toBe(false);
  expect(
    analyzeBundle(dataset, [local("base"), local("module")]),
  ).toMatchObject({
    exact: true,
    exactContributionGroups: [1, 2, 3],
    proxyContributionGroups: [],
  });
  const complete = analyzeBundle(dataset, [
    local("base"),
    local("contribution", 1),
    local("contribution", 2),
    local("contribution", 3),
  ]);
  expect(complete.exact).toBe(true);
  expect(complete.proxyContributionGroups).toEqual([]);
  const partial = analyzeBundle(dataset, [
    local("base"),
    local("contribution", 2),
  ]);
  expect(partial.exactContributionGroups).toEqual([2]);
  expect(partial.proxyContributionGroups).toEqual([1, 3]);
  expect(
    new Set([
      ...partial.exactContributionGroups,
      ...partial.proxyContributionGroups,
    ]).size,
  ).toBe(partial.requiredContributionGroups.length);
});
it("creates quantities and placements", () => {
  const dataset = datasetFromCounts([1, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);
  const manifest = createManifest(dataset);
  expect(manifest.totalCubeQuantity).toBe(3);
  expect(manifest.quantitiesByColorGroup).toEqual({ "1": 2, "2": 1 });
  expect(manifest.monthPlacements).toHaveLength(12);
});
