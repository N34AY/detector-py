import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    port: Number(process.env.VITE_DEV_PORT) || 5173,
    proxy: {
      '/api': {
        target: `http://${process.env.WEB_HOST || 'localhost'}:${process.env.WEB_PORT || 5001}`,
        changeOrigin: true
      },
      '/socket.io': {
        target: `http://${process.env.WEB_HOST || 'localhost'}:${process.env.WEB_PORT || 5001}`,
        ws: true,
        changeOrigin: true
      }
    }
  }
})
