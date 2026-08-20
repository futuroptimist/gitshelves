import { test, expect } from "@playwright/test";
test("shows sample and controls", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Synthetic sample")).toBeVisible();
  await expect(page.getByRole("button", { name: "Exploded" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Print plan" })).toBeVisible();
  await expect(page.locator("#state")).toHaveText("Design preview");
  await expect(
    page.getByRole("button", { name: "Download base STL" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Download module STL" }),
  ).toBeDisabled();
  await expect(page.locator("#geometry-note")).toContainText(
    "Proxy geometry is a non-printable Design preview",
  );
  await expect(page.locator("#geometry-note")).toContainText(
    "both canonical downloads are unavailable",
  );
  await expect(page.locator("#geometry-note")).toContainText(
    "npm run models:prepare",
  );
});

const triangle = (name: string) => ({
  name,
  mimeType: "model/stl",
  buffer: Buffer.from(
    "solid test\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\nendsolid test",
  ),
});

test("keeps partial and failed STL replacements in a consistent state", async ({
  page,
}) => {
  await page.goto("/");
  const input = page.locator("#stls");
  await input.setInputFiles([triangle("baseplate.stl")]);
  await expect(page.locator("#state")).toHaveText("Design preview");

  await input.setInputFiles([
    triangle("baseplate.stl"),
    triangle("contrib_cube.stl"),
  ]);
  await expect(page.locator("#state")).toHaveText("Exact STL geometry");

  await input.setInputFiles({
    name: "contrib_cube.stl",
    mimeType: "model/stl",
    buffer: Buffer.from("not an STL"),
  });
  await expect(page.locator("#message")).toContainText("not a valid STL");
  await expect(page.locator("#state")).toHaveText("Exact STL geometry");
  await expect(page.locator("#file-list")).toContainText("baseplate.stl");
});
