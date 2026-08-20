export const PITCH = 42;
export const HEIGHT_UNIT = 7;
export const SAMPLE_COUNTS = [
  0, 1, 9, 10, 99, 100, 999, 1000, 4, 42, 314, 2024,
] as const;
export interface MonthData {
  year: number;
  month: number;
  count: number;
  blocks: number;
}
export interface Dataset {
  title: string;
  months: MonthData[];
}
export function blocksForContributions(count: number): number {
  return count < 1 ? 0 : Math.floor(Math.log10(count)) + 1;
}
export function placement(month: number) {
  if (!Number.isInteger(month) || month < 1 || month > 12)
    throw new Error("Month must be 1–12");
  const index = month - 1;
  return {
    column: index % 6,
    row: Math.floor(index / 6),
    x: (index % 6) * PITCH,
    z: Math.floor(index / 6) * PITCH,
  };
}
export function moduleY(level: number, exploded: boolean): number {
  return 7 + level * HEIGHT_UNIT + (exploded ? level * 9 + 10 : 0);
}
export const SAMPLE: Dataset = {
  title: "Synthetic boundary sample",
  months: SAMPLE_COUNTS.map((count, index) => ({
    year: 2025,
    month: index + 1,
    count,
    blocks: blocksForContributions(count),
  })),
};
