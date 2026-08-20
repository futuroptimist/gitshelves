import { defineConfig } from "vite";
export default defineConfig({
  test: { environment: "jsdom", include: ["tests/*.test.ts"] },
  build: { sourcemap: true },
});
