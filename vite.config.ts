import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 3000,
    host: true,
  },
  build: {
    target: 'esnext',
    assetsInlineLimit: 0,
  },
  optimizeDeps: {
    exclude: ['@dimforge/rapier3d-compat'],
  },
});
