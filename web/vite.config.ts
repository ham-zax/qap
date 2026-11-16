import path from 'node:path'
import react from '@vitejs/plugin-react'
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  plugins: [
    tailwindcss(),
    tanstackRouter({
      target: 'react',
      autoCodeSplitting: true,
    }),
    react(),
  ],
  test: {
    environment: 'jsdom',
    setupFiles: './src/test-setup.ts',
  },
  server: {
    proxy: {
      '/api': process.env.QAP_API_PROXY_TARGET || 'http://127.0.0.1:8000',
    },
  },
})
