import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // Backend порт
        changeOrigin: true,
        secure: false,
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('Proxy error:', err);  // Лог proxy ошибок
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('Proxying request:', req.method, req.url);  // Лог запросов
          });
        },
      },
    },
  },
  css: {
    modules: {
      localsConvention: 'camelCase',
    },
  },
}); 