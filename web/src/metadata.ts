import { blocksForContributions, MONTHS, type Dataset } from "./model";
type UnknownRecord = Record<string, unknown>;
function record(value: unknown): UnknownRecord {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("JSON root must be an object");
  return value as UnknownRecord;
}
function monthlyFrom(value: unknown): number[] {
  if (Array.isArray(value)) {
    return value.map((v) => {
      if (typeof v === "number") return v;
      const r = record(v);
      return Number(r.contributions ?? r.count);
    });
  }
  const r = record(value);
  return MONTHS.map((label, i) =>
    Number(r[String(i + 1)] ?? r[label] ?? r[label.toLowerCase()] ?? 0),
  );
}
export function parseMetadata(text: string): Dataset {
  if (!text.trim()) throw new Error("Metadata file is empty");
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch {
    throw new Error("Metadata is not valid JSON");
  }
  const root = record(raw);
  const schema = root.schema_version ?? root.schemaVersion;
  if (schema && typeof schema !== "string")
    throw new Error("Unsupported metadata schema");
  const candidate =
    root.monthly_contributions ??
    root.months ??
    record(root.summary ?? {}).monthly_contributions;
  if (candidate === undefined)
    throw new Error("Metadata has no monthly contributions");
  const counts = monthlyFrom(candidate);
  if (counts.length !== 12 || counts.some((n) => !Number.isInteger(n) || n < 0))
    throw new Error("Metadata must contain twelve non-negative monthly counts");
  return {
    schemaVersion:
      typeof schema === "string" ? schema : "gitshelves-metadata/legacy",
    designVersion: "monthly-2x6-v1",
    source: "Local metadata",
    months: counts.map((contributions, i) => ({
      month: i + 1,
      label: MONTHS[i]!,
      contributions,
      blocks: blocksForContributions(contributions),
      colorGroup: Math.min(blocksForContributions(contributions), 4),
    })),
  };
}
