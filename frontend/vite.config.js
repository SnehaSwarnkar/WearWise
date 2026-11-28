import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const COMMERCE_PROXY = {
  target: process.env.VITE_COMMERCE_PROXY_TARGET || 'http://127.0.0.1:8001',
  changeOrigin: true,
}

const BODY_ENGINE_PROXY = {
  target: process.env.VITE_BODY_PROXY_TARGET || 'http://127.0.0.1:8000',
  changeOrigin: true,
}

const SHARED_PROXY = {
  '/api/auth': COMMERCE_PROXY,
  '/api/admin': COMMERCE_PROXY,
  '/api/seller': COMMERCE_PROXY,
  '/api/products': COMMERCE_PROXY,
  '/api/cart': COMMERCE_PROXY,
  '/api/orders': COMMERCE_PROXY,
  '/api/wardrobe': COMMERCE_PROXY,
  '/api/saved': COMMERCE_PROXY,
  '/api/avatar': COMMERCE_PROXY,
  '/api/assistant': COMMERCE_PROXY,
  '/api/catalogue': COMMERCE_PROXY,
  '/api/tryon': COMMERCE_PROXY,
  '/uploads': COMMERCE_PROXY,
  '/api': BODY_ENGINE_PROXY,
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '127.0.0.1',
    proxy: SHARED_PROXY,
  },
  preview: {
    port: 4173,
    host: '127.0.0.1',
    proxy: SHARED_PROXY,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    pool: 'vmThreads',
  },
})
