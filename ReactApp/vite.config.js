import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // proxy /chat → http://localhost:8000/chat
      "/chat": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false
      },
      // proxy /clear_history → http://localhost:8000/clear_history
      "/clear_history": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false
      },
    }
  }
});
