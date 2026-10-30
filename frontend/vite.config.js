import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Local dev: API at :8000 (Caddy strips /api in production the same way)
const proxy = {
  '/api': { target: 'http://127.0.0.1:8000', rewrite: (p) => p.replace(/^\/api/, '') },
}

export default defineConfig({
  plugins: [react()],
  server: { host: true, port: 5173, proxy },
  preview: { port: 4173, proxy },
})
