import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const backendTarget = process.env.VITE_DEV_BACKEND ?? 'http://127.0.0.1:10618'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@game-hall/plugin-sdk': fileURLToPath(new URL('./src/plugin-sdk/index.ts', import.meta.url)),
      '@lucide/vue': fileURLToPath(new URL('./node_modules/@lucide/vue', import.meta.url)),
      '@vue/test-utils': fileURLToPath(new URL('./node_modules/@vue/test-utils', import.meta.url)),
      'pinia': fileURLToPath(new URL('./node_modules/pinia', import.meta.url)),
      'vue': fileURLToPath(new URL('./node_modules/vue', import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    include: [
      'src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      '../third_party_games/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
    ],
  },
  server: {
    fs: { allow: [fileURLToPath(new URL('..', import.meta.url))] },
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': backendTarget,
      '/socket.io': {
        target: backendTarget,
        ws: true,
      },
    },
  },
})
