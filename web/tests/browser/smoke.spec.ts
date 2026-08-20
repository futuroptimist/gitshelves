import { test, expect } from "@playwright/test";
test("sample and primary controls render", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "GitShelves" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Assembled" })).toBeVisible();
  await page.getByRole("button", { name: "Text mode" }).click();
  await expect(page.getByRole("heading", { name: "Print plan" })).toBeVisible();
  await expect(
    page.getByText("Synthetic boundary sample", { exact: false }),
  ).toBeVisible();
});
