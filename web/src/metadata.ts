import { blocksForContributions, type Dataset, type MonthData } from "./model";
type UnknownRecord = Record<string, unknown>;
function record(value: unknown): UnknownRecord | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as UnknownRecord)
    : null;
}
function findMonths(root: UnknownRecord): unknown {
  if (Array.isArray(root.monthly_contributions))
    return root.monthly_contributions;
  if (Array.isArray(root.outputs)) {
    for (const output of root.outputs) {
      const item = record(output);
      if (item && Array.isArray(item.monthly_contributions))
        return item.monthly_contributions;
    }
  }
  return undefined;
}
export function parseMetadata(text: string): Dataset {
  if (!text.trim()) throw new Error("Metadata file is empty.");
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error("Metadata is not valid JSON.");
  }
  const root = record(parsed);
  if (!root) throw new Error("Metadata must be a JSON object.");
  const raw = findMonths(root);
  if (!Array.isArray(raw) || raw.length === 0)
    throw new Error("Unsupported metadata: monthly_contributions is required.");
  const seen = new Set<string>();
  const months: MonthData[] = raw.map((value) => {
    const item = record(value);
    const year = item?.year;
    const month = item?.month;
    const count = item?.count;
    if (
      !Number.isInteger(year) ||
      !Number.isInteger(month) ||
      !Number.isInteger(count) ||
      (count as number) < 0 ||
      (month as number) < 1 ||
      (month as number) > 12
    )
      throw new Error(
        "Each month needs integer year, month (1–12), and non-negative count.",
      );
    const key = `${year}-${month}`;
    if (seen.has(key)) throw new Error(`Duplicate month ${key}.`);
    seen.add(key);
    const blocks = blocksForContributions(count as number);
    if (item?.blocks !== undefined && item.blocks !== blocks)
      throw new Error(`Month ${key} has an inconsistent block count.`);
    return {
      year: year as number,
      month: month as number,
      count: count as number,
      blocks,
    };
  });
  if (months.length !== 12)
    throw new Error("The monthly 2×6 MVP requires exactly twelve months.");
  months.sort((a, b) => a.year - b.year || a.month - b.month);
  return {
    title:
      typeof root.username === "string"
        ? `${root.username} contribution year`
        : "Imported GitShelves run",
    months,
  };
}
