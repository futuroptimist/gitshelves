import { describe, expect, it } from "vitest";
import { blocksForContributions, moduleY, placement, SAMPLE } from "./model";
describe("canonical contribution transform", () => {
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
  it("places twelve months deterministically on 2x6", () =>
    expect(SAMPLE.months.map((m) => placement(m.month))).toEqual(
      Array.from({ length: 12 }, (_, i) => ({
        column: i % 6,
        row: Math.floor(i / 6),
        x: (i % 6) * 42,
        z: Math.floor(i / 6) * 42,
      })),
    ));
  it("separates exploded modules", () =>
    expect(moduleY(2, true)).toBeGreaterThan(moduleY(2, false)));
});
