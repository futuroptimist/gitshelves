// Validate the complete Docker export; never substitute preview geometry for STL.
import assert from 'node:assert/strict';
import { readFile, readdir, stat, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';

const root = path.resolve(process.argv[2] ?? 'site-artifact');
const dist = path.join(root, 'dist');
const html = await readFile(path.join(dist, 'index.html'), 'utf8');
assert.match(html, /GitShelves/);
for (const match of html.matchAll(/(?:src|href)="(\/assets\/[^"?#]+)"/g)) {
  assert.ok((await stat(path.join(dist, match[1]))).size > 0);
}
for (const name of ['baseplate_2x6', 'contrib_cube']) {
  const bytes = await readFile(path.join(dist, 'models', `${name}.stl`));
  assert.ok(bytes.length >= 84, `${name}: missing binary STL`);
  const count = bytes.readUInt32LE(80);
  assert.ok(count > 0 && bytes.length === 84 + 50 * count, `${name}: malformed STL`);
  const min = [Infinity, Infinity, Infinity];
  const max = [-Infinity, -Infinity, -Infinity];
  for (let offset = 84; offset < bytes.length; offset += 50) {
    for (let point = 0; point < 9; point++) {
      const value = bytes.readFloatLE(offset + 12 + point * 4);
      assert.ok(Number.isFinite(value), `${name}: non-finite coordinate`);
      const axis = point % 3;
      min[axis] = Math.min(min[axis], value);
      max[axis] = Math.max(max[axis], value);
    }
  }
  assert.ok(min.every((v, axis) => max[axis] - v > 0 && max[axis] - v <= 1000));
}
for (const name of ['gitshelves', 'gridfinity', 'three']) {
  assert.match(await readFile(path.join(dist, 'licenses', `${name}-MIT.txt`), 'utf8'), /Permission is hereby granted/);
}
const checksums = [];
async function inventory(dir) {
  for (const entry of (await readdir(dir, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) {
    const file = path.join(dir, entry.name);
    assert.ok(!entry.isSymbolicLink(), 'No symlinks in Site artifact');
    if (entry.isDirectory()) await inventory(file);
    else checksums.push(`${createHash('sha256').update(await readFile(file)).digest('hex')}  ${path.relative(root, file).split(path.sep).join('/')}`);
  }
}
await inventory(dist);
await writeFile(path.join(root, 'SHA256SUMS'), checksums.join('\n') + '\n');
console.log(`Validated ${checksums.length} files, canonical STL pair and MIT notices in ${dist}`);
