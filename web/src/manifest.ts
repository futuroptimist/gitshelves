import { placement, type Dataset } from "./model";
export function createManifest(dataset: Dataset, files: string[]) {
  const months = dataset.months.map((m) => ({
    ...m,
    placement: placement(m.month),
  }));
  const quantitiesByColorGroup: Record<string, number> = {};
  for (const month of months)
    for (let level = 1; level <= month.blocks; level++)
      quantitiesByColorGroup[String(Math.min(level, 4))] =
        (quantitiesByColorGroup[String(Math.min(level, 4))] ?? 0) + 1;
  return {
    schemaVersion: "gitshelves.print-manifest/v1",
    designVersion: "monthly-2x6-gridfinity-v1",
    title: dataset.title,
    months,
    totalCubeQuantity: months.reduce((sum, m) => sum + m.blocks, 0),
    quantitiesByColorGroup,
    referencedFiles: {
      base: files.filter((f) => /baseplate/i.test(f)),
      cubes: files.filter((f) => !/baseplate/i.test(f)),
    },
    assemblyGuidance:
      "Seat each month's first module in its labeled base cell, then add reusable modules vertically using the existing stackable lip. Verify fit before committing to a full print.",
  };
}
