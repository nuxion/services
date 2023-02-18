import { resolve } from 'path'
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
  root: resolve('./src'),
  base: '/',
  plugins: [svelte()],
  build: {
    manifest: true,
    outDir: resolve('./dist'),
    emptyOutDir: true,
    target: 'es2015',
    rollupOptions: {
      input: {
        main: resolve('./src/main.js'),
	    // explore: resolve('./theme/static/src/explore/main.js'),

      }
    }
  }
})
