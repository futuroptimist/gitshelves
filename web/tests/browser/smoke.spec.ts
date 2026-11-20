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

test("uses the centered username form and puts returned counts into the shelf", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const webgl = WebGL2RenderingContext.prototype;
    const canvas = window as unknown as Window & {
      shelfInstanceCounts: Set<number>;
    };
    canvas.shelfInstanceCounts = new Set();
    const elements = webgl.drawElementsInstanced;
    webgl.drawElementsInstanced = function (...args) {
      canvas.shelfInstanceCounts.add(args[4]);
      return elements.apply(this, args);
    };
    const arrays = webgl.drawArraysInstanced;
    webgl.drawArraysInstanced = function (...args) {
      canvas.shelfInstanceCounts.add(args[3]);
      return arrays.apply(this, args);
    };
  });
  const renderedInstances = () =>
    page.evaluate(() => [
      ...(window as unknown as Window & { shelfInstanceCounts: Set<number> })
        .shelfInstanceCounts,
    ]);
  await page.setViewportSize({ width: 1536, height: 920 });
  let requests = 0;
  await page.route("**/api/github-activity?*", async (route) => {
    requests++;
    expect(new URL(route.request().url()).searchParams.get("username")).toBe(
      "futuroptimist",
    );
    await route.fulfill({
      json: {
        username: "futuroptimist",
        start: "2026-10-22",
        counts: [...Array(29).fill(0), 24],
        sampled: 24,
        limited: false,
      },
    });
  });
  await page.goto("/");
  const form = page.getByRole("search");
  await expect(form).toBeVisible();
  expect(requests).toBe(0);
  await expect
    .poll(async () => (await renderedInstances()).some((count) => count > 2))
    .toBe(true);
  expect(await renderedInstances()).not.toContain(2);
  const input = page.getByLabel("Search GitHub activity");
  await input.fill("futuroptimist");
  await input.press("Enter");
  await expect(form.getByRole("status")).toContainText("24 public commits");
  await expect(
    page.getByRole("row", { name: "2026-11-20 24 2" }),
  ).toBeVisible();
  await expect(page.locator("#scene canvas")).toBeVisible();
  // The returned 24 public commits are two actual instances in the 3D scene.
  await expect.poll(renderedInstances).toContain(2);
  await expect.poll(renderedInstances).toContain(30);
  await expect(page.locator("#days tr")).toHaveCount(30);
  await expect(
    page.getByRole("button", { name: "Download print manifest" }),
  ).toBeDisabled();
  await expect(page.getByRole("button", { name: "Exploded" })).toBeVisible();
  const bounds = await form.boundingBox();
  expect(bounds).not.toBeNull();
  expect(
    Math.abs(bounds!.x + bounds!.width / 2 - page.viewportSize()!.width / 2),
  ).toBeLessThan(3);
  await page.setViewportSize({ width: 390, height: 844 });
  const mobileForm = await form.boundingBox();
  const model = await page.locator("#scene").boundingBox();
  const controls = await page.getByRole("complementary").boundingBox();
  expect(mobileForm).not.toBeNull();
  expect(model).not.toBeNull();
  expect(controls).not.toBeNull();
  expect(Math.abs(mobileForm!.x + mobileForm!.width / 2 - 195)).toBeLessThan(3);
  expect(mobileForm!.y + mobileForm!.height).toBeLessThanOrEqual(model!.y);
  expect(model!.y + model!.height).toBeLessThanOrEqual(controls!.y);
  await expect(form.getByRole("status")).toContainText("24 public commits");
  await page.getByRole("button", { name: "Clear activity" }).click();
  await expect(input).toHaveValue("");
  await expect(page.getByText("Synthetic sample")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Download print manifest" }),
  ).toBeEnabled();
});
