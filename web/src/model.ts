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
};
export type Dataset = {
  schemaVersion: string;
  designVersion: string;
  source: string;
  months: Month[];
};
export const SAMPLE_COUNTS = [
  0, 1, 9, 10, 99, 100, 999, 1000, 4, 42, 420, 7,
] as const;
export function blocksForContributions(count: number): number {
  if (!Number.isInteger(count) || count < 0)
    throw new Error("Contribution counts must be non-negative integers");
  return count === 0 ? 0 : Math.floor(Math.log10(count)) + 1;
}
export function placement(month: number) {
  if (!Number.isInteger(month) || month < 1 || month > 12)
    throw new Error("Month must be 1–12");
  const i = month - 1;
  return {
    column: i % 6,
    row: Math.floor(i / 6),
    x: (i % 6) * 42,
    y: Math.floor(i / 6) * 42,
  };
}
export function sampleDataset(): Dataset {
  return {
    schemaVersion: "gitshelves.web/v1",
    designVersion: "monthly-2x6-v1",
    source: "Synthetic boundary sample — not live GitHub data",
    months: SAMPLE_COUNTS.map((contributions, i) => ({
      month: i + 1,
      label: MONTHS[i]!,
      contributions,
      blocks: blocksForContributions(contributions),
      colorGroup: Math.min(blocksForContributions(contributions), 4),
    })),
  };
}
