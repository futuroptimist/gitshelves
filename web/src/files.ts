export type ComponentType = "baseplate" | "cube" | "contribution" | "unknown";
export interface LocalStl {
  name: string;
  type: ComponentType;
  colorGroup: number | null;
  bytes: Uint8Array;
  size: number;
}
export function classifyFilename(
  name: string,
): Pick<LocalStl, "type" | "colorGroup"> {
  const lower = name.toLowerCase();
  if (lower.includes("baseplate"))
    return { type: "baseplate", colorGroup: null };
  const group =
    lower.match(/_color(\d+)/)?.[1] ?? lower.match(/level(\d+)/)?.[1];
  if (group) return { type: "contribution", colorGroup: Number(group) };
  if (lower.includes("cube") || lower.includes("module"))
    return { type: "cube", colorGroup: 1 };
  return { type: "unknown", colorGroup: null };
}
export function isPlausibleStl(bytes: Uint8Array): boolean {
  if (bytes.length < 84) return false;
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const triangles = view.getUint32(80, true);
  return triangles > 0 && 84 + triangles * 50 === bytes.length;
}
export async function loadStlFile(file: File): Promise<LocalStl> {
  const bytes = new Uint8Array(await file.arrayBuffer());
  if (
    !isPlausibleStl(bytes) &&
    !new TextDecoder()
      .decode(bytes.slice(0, 80))
      .trimStart()
      .startsWith("solid")
  )
    throw new Error(`${file.name}: STL data is empty or malformed.`);
  return {
    name: file.name,
    ...classifyFilename(file.name),
    bytes,
    size: bytes.byteLength,
  };
}
export function downloadBytes(file: LocalStl): Uint8Array {
  return file.bytes.slice();
}
