export type ComponentType = "baseplate" | "cube" | "unknown";
export interface LoadedStl {
  name: string;
  type: ComponentType;
  colorGroup: number;
  bytes: Uint8Array;
}
export function classifyFilename(name: string): Omit<LoadedStl, "bytes"> {
  const lower = name.toLowerCase();
  const base = /baseplate/.test(lower);
  const match = lower.match(/(?:_color|level)(\d+)/);
  return {
    name,
    type: base
      ? "baseplate"
      : match || /cube|contrib/.test(lower)
        ? "cube"
        : "unknown",
    colorGroup: base ? 0 : match ? Number(match[1]) : 1,
  };
}
export function preserveStl(name: string, buffer: ArrayBuffer): LoadedStl {
  if (buffer.byteLength < 84)
    throw new Error(`${name}: STL is empty or too small.`);
  const view = new DataView(buffer);
  const triangles = view.getUint32(80, true);
  if (84 + triangles * 50 === buffer.byteLength) {
    if (triangles === 0) throw new Error(`${name}: STL contains no triangles.`);
    for (let offset = 84; offset < buffer.byteLength; offset += 50) {
      for (let coordinate = offset; coordinate < offset + 48; coordinate += 4) {
        if (!Number.isFinite(view.getFloat32(coordinate, true)))
          throw new Error(`${name}: STL contains non-finite geometry.`);
      }
    }
  }
  return { ...classifyFilename(name), bytes: new Uint8Array(buffer.slice(0)) };
}
export function downloadBytes(file: LoadedStl): Blob {
  return new Blob([file.bytes as BlobPart], { type: "model/stl" });
}
