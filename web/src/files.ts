export type ComponentType = "base" | "module" | "contribution" | "unknown";
export type LocalStl = {
  name: string;
  type: ComponentType;
  colorGroup: number;
  bytes: Uint8Array;
};
const textDecoder = new TextDecoder();
export function validateStlBytes(bytes: Uint8Array): void {
  if (bytes.byteLength < 84) throw new Error("STL is empty or too small.");
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const triangles = view.getUint32(80, true);
  const binaryLength = 84 + triangles * 50;
  const prefix = textDecoder
    .decode(bytes.subarray(0, Math.min(4096, bytes.length)))
    .trimStart();
  const plausibleAscii =
    prefix.startsWith("solid") &&
    prefix.includes("facet normal") &&
    prefix.includes("vertex") &&
    prefix.includes("endfacet");
  const validBinary = triangles > 0 && binaryLength === bytes.byteLength;
  if (!validBinary && !plausibleAscii)
    throw new Error("STL triangle data is malformed.");
}
export function classifyFilename(name: string): Omit<LocalStl, "bytes"> {
  const lower = name.toLowerCase();
  const group = Number(
    lower.match(/_color(\d+)/)?.[1] ?? lower.match(/level(\d+)/)?.[1] ?? 0,
  );
  const type: ComponentType = lower.includes("baseplate")
    ? "base"
    : lower.includes("contrib_cube")
      ? "module"
      : group > 0
        ? "contribution"
        : "unknown";
  return { name, type, colorGroup: type === "base" ? 0 : group };
}
export async function readStlFiles(files: File[]): Promise<LocalStl[]> {
  const seen = new Set<string>();
  const result: LocalStl[] = [];
  for (const file of files) {
    if (seen.has(file.name.toLowerCase()))
      throw new Error(`Duplicate file: ${file.name}`);
    seen.add(file.name.toLowerCase());
    if (!file.name.toLowerCase().endsWith(".stl"))
      throw new Error(`${file.name} is not an STL file.`);
    const bytes = new Uint8Array(await file.arrayBuffer());
    try {
      validateStlBytes(bytes);
    } catch {
      throw new Error(`${file.name} is empty or not a valid STL.`);
    }
    result.push({ ...classifyFilename(file.name), bytes });
  }
  return result;
}
