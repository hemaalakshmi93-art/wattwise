import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development, /api requests are proxied to the Flask server.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": process.env.VITE_PROXY_TARGET || "http://127.0.0.1:5001",
    },
  },
});
