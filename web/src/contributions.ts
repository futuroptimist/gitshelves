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
export function cubesForContributions(count: number): number {
  if (!Number.isFinite(count) || count < 0 || !Number.isInteger(count))
    throw new Error("Contribution counts must be non-negative integers.");
  return count === 0 ? 0 : Math.floor(Math.log10(count)) + 1;
}
export function placement(month: number) {
  if (!Number.isInteger(month) || month < 1 || month > 12)
    throw new Error("Month must be 1–12.");
  const index = month - 1;
  return {
    month,
    column: index % 6,
    row: Math.floor(index / 6),
    x: (index % 6) * 42,
    y: Math.floor(index / 6) * 42,
  };
}
