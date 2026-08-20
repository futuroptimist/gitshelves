import { cubesForContributions, MONTHS, placement } from "./contributions";
export interface MonthData {
  month: number;
  label: string;
  contributions: number;
  cubes: number;
  colorGroup: number;
  x: number;
  y: number;
  column: number;
  row: number;
}
export interface Dataset {
  title: string;
  months: MonthData[];
  source: "sample" | "metadata" | "run-summary";
}
export const SAMPLE_COUNTS = [
  0, 1, 9, 10, 99, 100, 999, 1000, 4, 42, 314, 2024,
];
export function datasetFromCounts(
  counts: number[],
  title = "Synthetic boundary sample",
  source: Dataset["source"] = "sample",
): Dataset {
  if (counts.length !== 12)
    throw new Error("A monthly 2×6 design requires exactly 12 months.");
  return {
    title,
    source,
    months: counts.map((contributions, index) => {
      const p = placement(index + 1);
      const cubes = cubesForContributions(contributions);
      return {
        ...p,
        label: MONTHS[index]!,
        contributions,
        cubes,
        colorGroup: Math.min(Math.max(cubes, 1), 4),
      };
    }),
  };
}
function monthlyValues(value: unknown): number[] | undefined {
  if (Array.isArray(value))
    return value.map((entry) =>
      typeof entry === "number"
        ? entry
        : typeof entry === "object" &&
            entry !== null &&
            "contributions" in entry
          ? Number((entry as { contributions: unknown }).contributions)
          : NaN,
    );
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    const entries = Object.entries(record).sort(([a], [b]) =>
      a.localeCompare(b),
    );
    if (entries.length === 12) return entries.map(([, count]) => Number(count));
  }
  return undefined;
}
export function parseMetadataText(text: string): Dataset {
  if (!text.trim()) throw new Error("The JSON file is empty.");
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error(
      "Malformed JSON: choose GitShelves metadata or a run summary.",
    );
  }
  if (!parsed || typeof parsed !== "object")
    throw new Error("Unsupported metadata schema.");
  const root = parsed as Record<string, unknown>;
  const candidates: unknown[] = [
    root.monthly_contributions,
    root.monthly,
    root.contributions,
  ];
  if (Array.isArray(root.files))
    for (const file of root.files)
      if (file && typeof file === "object")
        candidates.push(
          (file as Record<string, unknown>).monthly_contributions,
          (file as Record<string, unknown>).monthly,
        );
  const counts = candidates.map(monthlyValues).find(Boolean);
  if (!counts || counts.some((count) => !Number.isInteger(count) || count < 0))
    throw new Error(
      "Unsupported schema: expected twelve non-negative monthly contribution counts.",
    );
  return datasetFromCounts(
    counts,
    String(root.username ?? root.user ?? "Imported GitShelves design"),
    Array.isArray(root.files) ? "run-summary" : "metadata",
  );
}
export const SAMPLE_DATASET = datasetFromCounts(SAMPLE_COUNTS);
