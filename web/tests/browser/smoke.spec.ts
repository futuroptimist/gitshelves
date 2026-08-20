import { test, expect } from "@playwright/test";
test("shows sample and controls", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Synthetic sample")).toBeVisible();
  await expect(page.getByRole("button", { name: "Exploded" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Print plan" })).toBeVisible();
});
