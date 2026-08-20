import { describe, expect, it } from "vitest";
import { classifyFilename, downloadBytes, preserveStl } from "./files";
describe("STL bundles", () => {
  it.each([
    ["model_baseplate.stl", "baseplate", 0],
    ["model_color3.stl", "cube", 3],
    ["model-level5.stl", "cube", 5],
  ])("classifies %s", (name, type, color) =>
    expect(classifyFilename(name)).toMatchObject({ type, colorGroup: color }),
  );
  it("preserves exact bytes", async () => {
    const bytes = Uint8Array.from({ length: 84 }, (_, i) => i);
    new DataView(bytes.buffer).setUint32(80, 0, true);
    expect(() => preserveStl("empty-binary.stl", bytes.buffer)).toThrow(
      /no triangles/,
    );
    const printable = new Uint8Array(134);
    const view = new DataView(printable.buffer);
    view.setUint32(80, 1, true);
    view.setFloat32(96, 1, true);
    view.setFloat32(112, 2, true);
    view.setFloat32(128, 3, true);
    const loaded = preserveStl("cube.stl", printable.buffer);
    expect(new Uint8Array(await downloadBytes(loaded).arrayBuffer())).toEqual(
      printable,
    );
  });
  it("rejects implausible STL", () =>
    expect(() => preserveStl("bad.stl", new ArrayBuffer(2))).toThrow());
});
