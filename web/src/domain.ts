export const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
] as const;
export type Month = {
  month: number;
  label: string;
  contributions: number;
  blocks: number;
  colorGroup: number;
  x: number;
  y: number;
};
export type Dataset = {
  schemaVersion: string;
  designVersion: string;
  year: number;
  synthetic: boolean;
  months: Month[];
};
export function blocksForContributions(count: number): number {
  return count <= 0 ? 0 : Math.floor(Math.log10(count)) + 1;
}
export function placement(month: number) {
  return { x: ((month - 1) % 6) * 42, y: Math.floor((month - 1) / 6) * 42 };
}
export function datasetFromCounts(
  counts: number[],
  year = 2025,
  synthetic = false,
): Dataset {
  if (
    counts.length !== 12 ||
    counts.some((n) => !Number.isSafeInteger(n) || n < 0)
  )
    throw new Error("Expected exactly 12 non-negative integer monthly counts.");
  return {
    schemaVersion: "gitshelves.web/v1",
    designVersion: "monthly-2x6-v1",
    year,
    synthetic,
    months: counts.map((contributions, index) => {
      const month = index + 1;
      const blocks = blocksForContributions(contributions);
      return {
        month,
        label: MONTHS[index]!,
        contributions,
        blocks,
        colorGroup: Math.min(Math.max(blocks, 1), 4),
        ...placement(month),
      };
    }),
  };
}
export const SAMPLE = datasetFromCounts(
  [0, 1, 9, 10, 99, 100, 999, 1000, 4, 42, 314, 2024],
  2025,
  true,
);
