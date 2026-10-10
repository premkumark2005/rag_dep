import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    // Override at build time via VITE_API_BASE env var
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
