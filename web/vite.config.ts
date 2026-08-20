import { defineConfig } from "vitest/config";
export default defineConfig({
  base: "/",
  test: { exclude: ["e2e/**", "node_modules/**"] },
});
