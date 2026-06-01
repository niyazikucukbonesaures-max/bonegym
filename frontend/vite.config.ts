import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Vite yapılandırması — performans optimizasyonlu + Capacitor mobil desteği
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    target: 'esnext',
    minify: 'esbuild',
    // Capacitor için: dist/ klasörüne build et
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          query: ['@tanstack/react-query'],
          charts: ['recharts'],
          motion: ['framer-motion'],
          icons: ['lucide-react'],
          utils: ['axios', 'date-fns'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
    sourcemap: false,
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'axios',
      'date-fns',
      'recharts',
      'framer-motion',
      'lucide-react'
    ],
  },
  esbuild: {
    target: 'esnext',
    minify: true,
    treeShaking: true,
    drop: ['console', 'debugger'],
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
