import { test, expect } from "@playwright/test";
test("shows sample, primary controls, and useful text fallback", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "GitShelves" })).toBeVisible();
  await expect(
    page.getByText("Synthetic boundary sample", { exact: false }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Assembled" })).toBeVisible();
  await expect(page.locator("#months li")).toHaveCount(12);
  await page.getByRole("button", { name: "Text mode" }).click();
  await expect(page.locator("canvas")).toBeHidden();
  await expect(page.getByText("1,000 contributions")).toBeVisible();
});
test("honors reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.locator("html")).toHaveCSS("scroll-behavior", "auto");
});
