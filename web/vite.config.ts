import { defineConfig } from "vite";
export default defineConfig({
  test: { environment: "jsdom", include: ["tests/core.test.ts"] },
  build: { sourcemap: true },
});
