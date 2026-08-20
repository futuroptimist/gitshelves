import { defineConfig } from "vite";
export default defineConfig({
  base: "/",
  test: {
    environment: "node",
    exclude: ["tests/browser/**", "node_modules/**"],
  },
});
