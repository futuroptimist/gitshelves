import { mkdir, readFile, rm, stat } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
const root = resolve(import.meta.dirname, "../..");
const output = resolve(root, "web/public/models");
await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });
for (const [source, name] of [
  ["openscad/baseplate_2x6.scad", "baseplate_2x6.stl"],
  ["openscad/contrib_cube.scad", "contrib_cube.stl"],
]) {
  const command = process.env.DISPLAY ? "openscad" : "xvfb-run";
  const args = process.env.DISPLAY
    ? [
        "-o",
        resolve(output, name),
        "--export-format",
        "binstl",
        resolve(root, source),
      ]
    : [
        "-a",
        "openscad",
        "-o",
        resolve(output, name),
        "--export-format",
        "binstl",
        resolve(root, source),
      ];
  const result = spawnSync(command, args, { cwd: root, stdio: "inherit" });
  if (result.status !== 0)
    throw new Error(
      `Model preparation failed for ${source}; install OpenSCAD, Xvfb, and the pinned Gridfinity library.`,
    );
  if ((await stat(resolve(output, name))).size < 84)
    throw new Error(`${name} is not a plausible STL`);
  const bytes = await readFile(resolve(output, name));
  const triangles = bytes.readUInt32LE(80);
  if (!triangles || 84 + triangles * 50 !== bytes.length)
    throw new Error(`${name} is not a nonempty binary STL`);
  const minimum = [Infinity, Infinity, Infinity];
  const maximum = [-Infinity, -Infinity, -Infinity];
  for (let triangle = 0; triangle < triangles; triangle++) {
    const start = 84 + triangle * 50 + 12;
    for (let vertex = 0; vertex < 3; vertex++) {
      for (let axis = 0; axis < 3; axis++) {
        const value = bytes.readFloatLE(start + vertex * 12 + axis * 4);
        if (!Number.isFinite(value))
          throw new Error(`${name} has non-finite bounds`);
        minimum[axis] = Math.min(minimum[axis], value);
        maximum[axis] = Math.max(maximum[axis], value);
      }
    }
  }
  if (maximum.every((value, axis) => value === minimum[axis]))
    throw new Error(`${name} has zero bounds`);
}
console.log(`Prepared canonical models in ${output}`);
