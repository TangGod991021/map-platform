import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/prod-api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/profile': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/map-api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
