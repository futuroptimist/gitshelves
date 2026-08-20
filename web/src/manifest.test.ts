import { expect, it } from "vitest";
import { createManifest } from "./manifest";
import { SAMPLE } from "./model";
it("creates deterministic print quantities and placements", () => {
  const manifest = createManifest(SAMPLE, [
    "baseplate_2x6.stl",
    "contrib_cube.stl",
  ]);
  expect(manifest.totalCubeQuantity).toBe(
    SAMPLE.months.reduce((n, m) => n + m.blocks, 0),
  );
  expect(manifest.months[11]?.placement).toEqual({
    column: 5,
    row: 1,
    x: 210,
    z: 42,
  });
  expect(manifest.referencedFiles.base).toEqual(["baseplate_2x6.stl"]);
});
