import { expect, it } from "vitest";
import { readStlFiles } from "../src/files";
const bytes = new Uint8Array(134);
const view = new DataView(bytes.buffer);
view.setUint32(80, 1, true);
view.setFloat32(108, 1, true);
view.setFloat32(124, 1, true);
const file = (name: string, content: Uint8Array = bytes) =>
  Object.assign(new Blob([content.slice().buffer]), { name }) as File;
it("preserves exact STL bytes", async () => {
  const [loaded] = await readStlFiles([file("thing_color2.stl")]);
  expect(loaded?.bytes).toEqual(bytes);
});
it("rejects duplicate and malformed files", async () => {
  await expect(
    readStlFiles([file("same.stl"), file("SAME.stl")]),
  ).rejects.toThrow("Duplicate");
  await expect(
    readStlFiles([file("bad.stl", new Uint8Array(3))]),
  ).rejects.toThrow("valid STL");
  await expect(
    readStlFiles([file("empty.stl", new Uint8Array(84))]),
  ).rejects.toThrow("valid STL");
});
