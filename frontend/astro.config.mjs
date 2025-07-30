import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  integrations: [
    react(),
    tailwind()
  ],
  base: './', // Use relative paths for Electron
  build: {
    assets: '_astro', // Keep assets in _astro folder
    assetsPrefix: './' // Ensure all assets use relative paths
  },
  vite: {
    optimizeDeps: {
      exclude: ['monaco-editor']
    },
    build: {
      rollupOptions: {
        external: ['monaco-editor'],
        output: {
          assetFileNames: '_astro/[name]-[hash][extname]',
          chunkFileNames: '_astro/[name]-[hash].js',
          entryFileNames: '_astro/[name]-[hash].js'
        }
      }
    }
  }
});

