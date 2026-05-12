import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    // Railway (and similar) inject PORT; local default 3000.
    port: Number(process.env.PORT) || 3000,
    strictPort: false,
    proxy: {
      "/api": {
        // Use localhost when running frontend with npm run dev; backend:8000 only works inside Docker.
        target: process.env.VITE_API_TARGET || "http://localhost:8000",
        changeOrigin: true,
        // Match nginx: long AI requests (process-ai) must not time out at ~60s.
        proxyTimeout: 300000,
        timeout: 300000,
      },
      "/media": {
        target: process.env.VITE_API_TARGET || "http://localhost:8000",
        changeOrigin: true,
        proxyTimeout: 120000,
        timeout: 120000,
      },
    },
  },
});
