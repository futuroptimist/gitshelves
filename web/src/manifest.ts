import type { Dataset } from "./domain";
import type { LocalStl } from "./files";
export function createManifest(dataset: Dataset, files: LocalStl[] = []) {
  const quantitiesByColorGroup: Record<string, number> = {};
  for (const month of dataset.months)
    for (let level = 1; level <= month.blocks; level++) {
      const group = String(Math.min(level, 4));
      quantitiesByColorGroup[group] = (quantitiesByColorGroup[group] ?? 0) + 1;
    }
  return {
    schemaVersion: "gitshelves.print-manifest/v1",
    designVersion: dataset.designVersion,
    year: dataset.year,
    monthPlacements: dataset.months,
    totalCubeQuantity: dataset.months.reduce((sum, m) => sum + m.blocks, 0),
    quantitiesByColorGroup,
    referencedFiles: files.map((f) => ({
      filename: f.name,
      componentType: f.type,
      colorGroup: f.colorGroup,
      bytes: f.bytes.byteLength,
    })),
    canonicalFiles: { base: "baseplate_2x6.stl", module: "contrib_cube.stl" },
    assemblyGuidance:
      "Seat the first module in its labeled base cell, then place each additional module on the stackable lip. Verify fit before completing the assembly.",
  };
}
