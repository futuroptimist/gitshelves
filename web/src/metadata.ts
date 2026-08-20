import { datasetFromCounts, type Dataset } from "./domain";
type UnknownRecord = Record<string, unknown>;
const record = (v: unknown): UnknownRecord | undefined =>
  typeof v === "object" && v !== null ? (v as UnknownRecord) : undefined;
function monthlyFrom(
  value: unknown,
): { year: number; counts: number[] } | undefined {
  const root = record(value);
  if (!root) return;
  const candidates = [
    root.monthly_contributions,
    record(root.contributions)?.monthly,
    record(root.metadata)?.monthly_contributions,
    ...(Array.isArray(root.outputs)
      ? root.outputs.map((output) => record(output)?.monthly_contributions)
      : []),
  ];
  for (const candidate of candidates) {
    if (Array.isArray(candidate)) {
      const items = candidate.map(record).filter((item) => item !== undefined);
      const years = items
        .map((item) => Number(item.year))
        .filter(Number.isInteger);
      if (!years.length) continue;
      const year = Math.max(...years);
      const counts = Array(12).fill(0) as number[];
      for (const item of items) {
        const month = Number(item.month);
        const count = Number(item.count);
        if (
          Number(item.year) === year &&
          month >= 1 &&
          month <= 12 &&
          Number.isSafeInteger(count) &&
          count >= 0
        )
          counts[month - 1] = count;
      }
      return { year, counts };
    }
    const data = record(candidate);
    if (!data) continue;
    const entries = Object.entries(data);
    if (!entries.length) continue;
    const years = entries
      .map(([key]) => Number(key.match(/\d{4}/)?.[0]))
      .filter(Number.isFinite);
    const year = years[0] ?? Number(root.year);
    const counts = Array(12).fill(0) as number[];
    for (const [key, raw] of entries) {
      const nums = key.match(/\d+/g)?.map(Number) ?? [];
      const month = (nums.length > 1 ? nums[1] : Number(key)) ?? 0;
      if (month >= 1 && month <= 12 && typeof raw === "number")
        counts[month - 1] = raw;
    }
    if (Number.isInteger(year)) return { year, counts };
  }
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
  if (
    root.schemaVersion === "gitshelves.web/v1" &&
    Array.isArray(root.months)
  ) {
    const year = Number(root.year);
    const counts = root.months.map((m) => Number(record(m)?.contributions));
    return datasetFromCounts(counts, year);
  }
  const found = monthlyFrom(parsed);
  if (!found)
    throw new Error(
      "Unsupported metadata schema: monthly contribution counts were not found.",
    );
  return datasetFromCounts(found.counts, found.year);
}
