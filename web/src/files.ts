export type ComponentType = "base" | "module" | "contribution" | "unknown";
export type LocalStl = {
  name: string;
  type: ComponentType;
  colorGroup: number;
  bytes: Uint8Array;
};
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import * as THREE from "three";
const textDecoder = new TextDecoder();
export function appendLiteralFilename(
  parent: HTMLElement,
  name: string,
): HTMLElement {
  const item = document.createElement("li");
  item.textContent = name;
  parent.append(item);
  return item;
}
export function validateStlBytes(bytes: Uint8Array): void {
  const prefix = textDecoder
    .decode(bytes.subarray(0, Math.min(4096, bytes.length)))
    .trimStart();
  const plausibleAscii = prefix.startsWith("solid");
  let validBinary = false;
  if (bytes.byteLength >= 84) {
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const triangles = view.getUint32(80, true);
    validBinary = triangles > 0 && 84 + triangles * 50 === bytes.byteLength;
  }
  if (!validBinary && !plausibleAscii)
    throw new Error("STL triangle data is malformed.");
}
export function parseStlGeometry(bytes: Uint8Array): THREE.BufferGeometry {
  validateStlBytes(bytes);
  let geometry: THREE.BufferGeometry;
  try {
    geometry = new STLLoader().parse(bytes.slice().buffer);
  } catch {
    throw new Error("STL geometry could not be parsed.");
  }
  const positions = geometry.getAttribute("position");
  if (!positions || positions.count < 3 || positions.count % 3 !== 0) {
    geometry.dispose();
    throw new Error("STL contains no triangles.");
  }
  for (const value of positions.array)
    if (!Number.isFinite(value)) {
      geometry.dispose();
      throw new Error("STL contains non-finite coordinates.");
    }
  geometry.computeBoundingBox();
  const size = geometry.boundingBox!.getSize(new THREE.Vector3());
  const largest = Math.max(size.x, size.y, size.z);
  if (!(largest > 1e-6) || largest > 1_000_000) {
    geometry.dispose();
    throw new Error("STL bounds are zero or implausible.");
  }
  return geometry;
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
      parseStlGeometry(bytes).dispose();
    } catch (error) {
      throw new Error(
        `${file.name} is not a valid STL: ${(error as Error).message}`,
      );
    }
    result.push({ ...classifyFilename(file.name), bytes });
  }
  return result;
}
