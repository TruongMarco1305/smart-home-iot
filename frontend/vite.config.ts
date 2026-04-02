import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // VITE_API_BASE_URL is set at build time for production (Firebase).
  // In dev, requests to /api are proxied to localhost:8000.
  define: {
    __API_BASE__: JSON.stringify(process.env.VITE_API_BASE_URL ?? ''),
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
