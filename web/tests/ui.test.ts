import { expect, it } from "vitest";
import { readFileSync } from "node:fs";
const html = readFileSync("src/main.ts", "utf8");
const css = readFileSync("src/style.css", "utf8");
it("contains initial sample, primary controls, and text fallback", () => {
  for (const text of [
    "Design preview",
    "Synthetic sample",
    "Assembled",
    "Exploded",
    "Reset camera",
    "Fit model",
    "Print plan",
  ])
    expect(html).toContain(text);
});
it("honors reduced motion", () =>
  expect(css).toContain("prefers-reduced-motion: reduce"));
