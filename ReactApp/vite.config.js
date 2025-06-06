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
      // proxy /visualize/questions → http://localhost:8000/visualize/questions
      "/visualize/questions": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false
      },
      // proxy /visualize/complete → http://localhost:8000/visualize/complete
      "/visualize/complete": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false
      },
      "/infograph/questions": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false
      },
      "/infograph/complete": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false
      },
      "/summarize": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false
      },
      "/intro": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false
      },
      // serve chart and table images from FastAPI
      "/charts": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false
      },
    }
  }
});
