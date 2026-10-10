import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("http://127.0.0.1:4173/");
  await page
    .locator("#state")
    .filter({ hasText: "Exact STL geometry" })
    .waitFor();
  assert.equal(await page.locator("#sample").textContent(), "Synthetic sample");
  await page.getByRole("button", { name: "Exploded", exact: true }).click();
  assert.equal(
    await page.locator("#exploded").getAttribute("aria-pressed"),
    "true",
  );
  for (const [label, name] of [
    ["Download base STL", "baseplate_2x6.stl"],
    ["Download module STL", "contrib_cube.stl"],
  ]) {
    const pending = page.waitForEvent("download");
    await page.getByRole("button", { name: label, exact: true }).click();
    const download = await pending;
    assert.equal(await download.failure(), null);
    const expected = await readFile(
      new URL(`../../site-artifact/dist/models/${name}`, import.meta.url),
    );
    assert.deepEqual(await readFile(await download.path()), expected);
  }
  assert.deepEqual(errors, []);
} finally {
  await browser.close();
}
