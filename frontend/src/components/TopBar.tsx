import { Menu, LogOut, User, Bell } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

interface TopBarProps {
  title: string
  onMenuClick: () => void
}

export function TopBar({ title, onMenuClick }: TopBarProps) {
  const { user, logout } = useAuth()

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between px-5 h-14 bg-[#0f0f14]/95 backdrop-blur-sm border-b border-white/[0.06]">
      {/* Left */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-1.5 rounded-md text-white/40 hover:text-white hover:bg-white/[0.06] transition-colors"
        >
          <Menu className="w-4 h-4" />
        </button>
        <h1 className="text-[14px] font-semibold text-white/90 tracking-tight">{title}</h1>
      </div>

      {/* Right */}
      <div className="flex items-center gap-1">
        {/* Notification bell */}
        <button className="p-2 rounded-lg text-white/35 hover:text-white/70 hover:bg-white/[0.05] transition-colors">
          <Bell className="w-4 h-4" />
        </button>

        {/* User */}
        {user && (
          <div className="flex items-center gap-2 ml-1 pl-3 border-l border-white/[0.08]">
            <div className="w-7 h-7 rounded-full bg-violet-600/30 border border-violet-500/30 flex items-center justify-center">
              <User className="w-3.5 h-3.5 text-violet-300" />
            </div>
            <span className="hidden sm:block text-[13px] text-white/60 font-medium">
              {user.full_name || user.username}
            </span>
          </div>
        )}

        {/* Logout */}
        {user && (
          <button
            onClick={logout}
            className="ml-1 flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[12px] text-white/35 hover:text-white/70 hover:bg-white/[0.05] transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Çıkış</span>
          </button>
        )}
      </div>
    </header>
  )
}
