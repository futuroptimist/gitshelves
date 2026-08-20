export type ComponentType = "baseplate" | "cube" | "contribution" | "unknown";
export type Classified = {
  name: string;
  component: ComponentType;
  colorGroup: number | null;
  bytes: Uint8Array;
};
export function classifyFilename(name: string): Omit<Classified, "bytes"> {
  const lower = name.toLowerCase();
  const color = lower.match(/_color(\d+)/);
  const level = lower.match(/level(\d+)/);
  const group = Number(color?.[1] ?? level?.[1] ?? 0) || null;
  let component: ComponentType = "unknown";
  if (/baseplate/.test(lower)) component = "baseplate";
  else if (/contrib[_-]?cube|module/.test(lower)) component = "cube";
  else if (group !== null || /contribution/.test(lower))
    component = "contribution";
  return {
    name,
    component,
    colorGroup: component === "baseplate" ? null : group,
  };
}
export function preserveFile(name: string, buffer: ArrayBuffer): Classified {
  const bytes = new Uint8Array(buffer.slice(0));
  return { ...classifyFilename(name), bytes };
}
export function validateStl(bytes: Uint8Array): void {
  if (bytes.byteLength < 84) throw new Error("STL is empty or too small");
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const triangles = view.getUint32(80, true);
  if (
    84 + triangles * 50 !== bytes.byteLength &&
    !new TextDecoder()
      .decode(bytes.slice(0, 5))
      .toLowerCase()
      .startsWith("solid")
  )
    throw new Error("STL structure is malformed");
}
