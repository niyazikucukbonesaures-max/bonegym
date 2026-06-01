import { useState, ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'

// Route → sayfa başlığı eşlemesi
const pageTitles: Record<string, string> = {
  '/dashboard': 'Pano',
  '/food-log': 'Kalori Günlüğü',
  '/ai-assistant': 'AI Besin Asistanı',
  '/workouts': 'Antrenman',
  '/creatine': 'Kreatin',
  '/measurements': 'Ölçümler',
  '/profile': 'Profil',
  '/export': 'Dışa Aktarma',
}

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const title = pageTitles[location.pathname] ?? 'FitTrack'

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Ana içerik — desktop'ta sidebar genişliği kadar sol boşluk */}
      <div className="flex flex-col flex-1 lg:pl-64 min-w-0">
        <TopBar title={title} onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  )
}
