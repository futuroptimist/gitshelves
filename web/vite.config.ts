import { defineConfig } from "vite";
export default defineConfig({
  base: "/",
  server: { proxy: { "/api/github-activity": "http://127.0.0.1:8080" } },
  test: {
    environment: "node",
    exclude: ["tests/browser/**", "node_modules/**"],
  },
});
