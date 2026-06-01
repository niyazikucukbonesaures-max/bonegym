import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App.tsx'
import { ThemeProvider } from './components/ThemeProvider.tsx'
import './index.css'
import './styles/performance.css'

// React Query istemcisi — mobil app için optimize edilmiş ayarlar
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 5 dakika stale — backend cache ile uyumlu
      staleTime: 5 * 60 * 1000,
      // 30 dakika bellekte tut
      gcTime: 30 * 60 * 1000,
      // Hata durumunda 2 kez yeniden dene (mobil ağ kesintileri için)
      retry: 2,
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 10000),
      // Pencere odaklandığında yeniden fetch etme (pil tasarrufu)
      refetchOnWindowFocus: false,
      // Mount'ta cache varsa fetch etme
      refetchOnMount: false,
      // Ağ yeniden bağlandığında fetch et (mobil için önemli)
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 0,
    },
  },
})

// Uygulama kök elementi — React 18 concurrent mode
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {/* React Query sağlayıcısı — tüm uygulamaya veri yönetimi sağlar */}
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        {/* React Router — istemci taraflı yönlendirme */}
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  </React.StrictMode>,
)