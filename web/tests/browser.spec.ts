import { test, expect } from "@playwright/test";
test("sample and primary controls render", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "GitShelves" })).toBeVisible();
  await expect(page.getByText("Synthetic", { exact: false })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Exploded" })).toBeVisible();
  await expect(page.locator("#month-list tr")).toHaveCount(12);
  await page.getByText(/Text mode and print plan/).click();
  await expect(page.getByText("1,000")).toBeVisible();
  await expect(page.getByText("Design preview")).toBeVisible();
});
