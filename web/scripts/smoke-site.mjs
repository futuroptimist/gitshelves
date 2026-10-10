import { chromium } from "@playwright/test";
import assert from "node:assert/strict";

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
  for (const label of ["Download base STL", "Download module STL"]) {
    const pending = page.waitForEvent("download");
    await page.getByRole("button", { name: label, exact: true }).click();
    assert.equal(await (await pending).failure(), null);
  }
  assert.deepEqual(errors, []);
} finally {
  await browser.close();
}
