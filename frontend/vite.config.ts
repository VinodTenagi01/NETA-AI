import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const phase2Notice = {
  name: "neta-phase2-notice",
  configureServer(server: any) {
    server.httpServer?.once("listening", () => {
      process.stdout.write(
        "\n  \x1b[1m\x1b[35m NETA.AI Phase 2 Dev Server\x1b[0m\n" +
        "  \x1b[1mPort 5176 — Phase 2 backend (localhost:8000)\x1b[0m\n" +
        "  \x1b[33mFor Phase 1 dashboard use: http://127.0.0.1:5175\x1b[0m\n\n"
      );
    });
  },
};

export default defineConfig(() => {
  return {
    plugins: [react(), phase2Notice],
    server: {
      host: '127.0.0.1',  // IPv4 only — prevents binding [::1] alongside neta-ai-mockup
      port: 5176,         // Phase 2 port — neta-ai-mockup owns 5175
      strictPort: true,   // fail hard if 5176 is occupied; never auto-increment
      proxy: {
        "/api": {
          target: "http://localhost:8000",
          changeOrigin: true,
          secure: false,
        },
      },
    },
    build: {
      outDir: "dist",
      sourcemap: true,
    },
  };
});
