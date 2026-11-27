import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  // Lit le .env à la racine du dépôt ; seules les variables VITE_* sont exposées au navigateur.
  envDir: "..",
  server: {
    port: 5173,
    host: "127.0.0.1",
  },
});
