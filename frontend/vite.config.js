import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Разрешает доступ по сети
    port: 5173,
    allowedHosts: [
      '.ngrok-free.dev', // Разрешает все поддомены ngrok-free.dev
      // '.ngrok-free.app', // Можно добавить и старый домен на всякий случай
    ],
    // Ниже — настройка прокси, чтобы фронтенд мог обращаться к бэкенду
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // Порт вашего бэкенда
        changeOrigin: true,
      },
    },
  },
})