import type { Dataset } from "./metadata";
export interface PrintManifest {
  schemaVersion: "1.0";
  designVersion: "monthly-2x6-v1";
  title: string;
  placements: Dataset["months"];
  totalCubes: number;
  quantitiesByColorGroup: Record<string, number>;
  files: { base: string | null; cube: string | null };
  assembly: string[];
}
export function createManifest(
  dataset: Dataset,
  exactFiles: boolean,
): PrintManifest {
  const quantities: Record<string, number> = {};
  for (const month of dataset.months)
    for (let level = 1; level <= month.cubes; level++) {
      const key = String(Math.min(level, 4));
      quantities[key] = (quantities[key] ?? 0) + 1;
    }
  return {
    schemaVersion: "1.0",
    designVersion: "monthly-2x6-v1",
    title: dataset.title,
    placements: dataset.months,
    totalCubes: dataset.months.reduce((sum, month) => sum + month.cubes, 0),
    quantitiesByColorGroup: quantities,
    files: {
      base: exactFiles ? "models/baseplate_2x6.stl" : null,
      cube: exactFiles ? "models/contrib_cube.stl" : null,
    },
    assembly: [
      "Seat the first module for each month in its labeled 2×6 base position.",
      "Stack remaining reusable modules vertically using the existing stackable lip.",
      "This interface is not yet documented as test-printed or fit-validated.",
    ],
  };
}
