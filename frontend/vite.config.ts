import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/game': 'http://127.0.0.1:8000',
      '/dungeons': 'http://127.0.0.1:8000',
      '/party': 'http://127.0.0.1:8000',
      '/expedition-plan': 'http://127.0.0.1:8000',
      '/reports': 'http://127.0.0.1:8000',
      '/quests': 'http://127.0.0.1:8000',
      '/shop': 'http://127.0.0.1:8000',
      '/recruits': 'http://127.0.0.1:8000',
      '/debug': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000'
    }
  }
})
