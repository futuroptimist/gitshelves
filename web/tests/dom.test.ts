import { expect, it } from "vitest";
import { readFileSync } from "node:fs";
it("ships the sample, controls, accessibility status, and reduced-motion fallback", () => {
  const main = readFileSync("src/main.ts", "utf8");
  const css = readFileSync("src/style.css", "utf8");
  for (const text of [
    "Assembled",
    "Exploded",
    "Reset camera",
    "Fit to model",
    "Text mode",
    "aria-live",
  ])
    expect(main).toContain(text);
  expect(main).toContain("sampleDataset");
  expect(css).toContain("prefers-reduced-motion");
});
