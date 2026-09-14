import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  server: {
    // 0.0.0.0 so the forwarded 5173 port is reachable from the browser.
    host: true,
    port: 5173,
    strictPort: true,
    proxy: {
      // Browser stays on one origin. FastAPI has no /api prefix.
      '/api': {
        target: 'http://127.0.0.1:8000',
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
