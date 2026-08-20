import { placement, type Dataset } from "./model";
import type { Classified } from "./files";
export function createManifest(data: Dataset, files: Classified[] = []) {
  const quantitiesByColorGroup: Record<string, number> = {};
  for (const m of data.months)
    for (let level = 1; level <= m.blocks; level++) {
      const key = String(Math.min(level, 4));
      quantitiesByColorGroup[key] = (quantitiesByColorGroup[key] ?? 0) + 1;
    }
  return {
    schemaVersion: "gitshelves.print-manifest/v1",
    designVersion: data.designVersion,
    source: data.source,
    months: data.months.map((m) => ({ ...m, placement: placement(m.month) })),
    totalCubeQuantity: data.months.reduce((n, m) => n + m.blocks, 0),
    quantitiesByColorGroup,
    files: {
      base: files.filter((f) => f.component === "baseplate").map((f) => f.name),
      cubes: files
        .filter((f) => f.component === "cube" || f.component === "contribution")
        .map((f) => f.name),
    },
    assembly: [
      "Print one 2×6 base and the listed reusable modules.",
      "Seat each month’s first module on its marked base position.",
      "Use each module’s existing stackable lip for subsequent levels; inspect fit before use.",
    ],
  };
}
