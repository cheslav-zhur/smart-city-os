import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vitest/config'

const apiProxyTarget =
  (globalThis as { process?: { env?: { API_PROXY_TARGET?: string } } }).process
    ?.env?.API_PROXY_TARGET ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    // 0.0.0.0 so the forwarded 5173 port is reachable from the browser.
    host: true,
    port: 5173,
    strictPort: true,
    proxy: {
      // Browser stays on one origin. FastAPI has no /api prefix.
      // Compose `web` service sets API_PROXY_TARGET=http://api:8000.
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/setupTests.ts',
  },
})
