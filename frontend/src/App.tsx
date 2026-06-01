import { Routes, Route, Navigate } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { Layout } from './components/Layout'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AnimationProvider } from './contexts/AnimationContext'
import { EnhancedErrorBoundary } from './components/EnhancedErrorBoundary'
import { SkeletonLoader } from './components/ui/SkeletonLoader'

// Sayfa bileşenleri — lazy loading ile performans optimizasyonu
const Dashboard = lazy(() => import('./pages/Dashboard'))
const FoodLog = lazy(() => import('./pages/FoodLog'))
const AIAssistant = lazy(() => import('./pages/AIAssistant'))
const Workouts = lazy(() => import('./pages/Workouts'))
const Creatine = lazy(() => import('./pages/Creatine'))
const Measurements = lazy(() => import('./pages/Measurements'))
const Profile = lazy(() => import('./pages/Profile'))
const Export = lazy(() => import('./pages/Export'))
const Login = lazy(() => import('./pages/Login'))
const MealPlan = lazy(() => import('./pages/MealPlan'))
const Achievements = lazy(() => import('./pages/Achievements'))

// Yükleme göstergesi — sayfa geçişlerinde gösterilir
function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-violet-950 via-purple-900 to-indigo-950">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-violet-500 mx-auto mb-4" />
        <p className="text-white/70">Yükleniyor...</p>
      </div>
    </div>
  )
}

// Ana uygulama içeriği - BASİT VE ÇALIŞAN
function AppContent() {
  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Login sayfası */}
          <Route path="/login" element={<Login />} />
          
          {/* Ana sayfa - dashboard'a yönlendir */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* Tüm sayfalar - Layout içinde */}
          <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
          <Route path="/food-log" element={<ProtectedRoute><Layout><FoodLog /></Layout></ProtectedRoute>} />
          <Route path="/ai-assistant" element={<ProtectedRoute><Layout><AIAssistant /></Layout></ProtectedRoute>} />
          <Route path="/workouts" element={<ProtectedRoute><Layout><Workouts /></Layout></ProtectedRoute>} />
          <Route path="/creatine" element={<ProtectedRoute><Layout><Creatine /></Layout></ProtectedRoute>} />
          <Route path="/measurements" element={<ProtectedRoute><Layout><Measurements /></Layout></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Layout><Profile /></Layout></ProtectedRoute>} />
          <Route path="/meal-plan" element={<ProtectedRoute><Layout><MealPlan /></Layout></ProtectedRoute>} />
          <Route path="/achievements" element={<ProtectedRoute><Layout><Achievements /></Layout></ProtectedRoute>} />
          <Route path="/export" element={<ProtectedRoute><Layout><Export /></Layout></ProtectedRoute>} />

          {/* Bilinmeyen rotalar */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </div>
  )
}

// Ana uygulama bileşeni
export default function App() {
  return (
    <EnhancedErrorBoundary
      showReportButton={true}
      enableRecovery={true}
      onError={(error, errorInfo) => {
        // Log error to monitoring service
        console.error('Application error:', error, errorInfo)
      }}
    >
      <AuthProvider>
        <AnimationProvider
          config={{
            maxConcurrentAnimations: 50,
            targetFPS: 60,
            enableGPUAcceleration: true,
            respectReducedMotion: true,
            performanceMonitoring: true,
            debugMode: false
          }}
        >
          <AppContent />
        </AnimationProvider>
      </AuthProvider>
    </EnhancedErrorBoundary>
  )
}