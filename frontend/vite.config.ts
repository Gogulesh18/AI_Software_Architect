import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api to the FastAPI backend so the frontend never
// needs to know the backend port/host outside of this one place.
export default defineConfig({
  plugins: [react()],
  resolve: {
    // Mirrors tsconfig.app.json's "paths" mapping — TS path aliases only
    // affect type-checking, Vite/Rollup needs their own alias to resolve
    // "@/..." imports at bundle time.
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
