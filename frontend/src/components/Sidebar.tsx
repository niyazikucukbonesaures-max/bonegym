import { NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  UtensilsCrossed,
  Dumbbell,
  Pill,
  Ruler,
  User,
  Download,
  X,
  ChefHat,
  Trophy,
  Bot,
  Activity,
} from 'lucide-react'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

const navItems = [
  { to: '/dashboard', label: 'Genel Bakış', icon: LayoutDashboard },
  { to: '/food-log', label: 'Besin Günlüğü', icon: UtensilsCrossed },
  { to: '/ai-assistant', label: 'AI Asistan', icon: Bot },
  { to: '/workouts', label: 'Antrenman', icon: Dumbbell },
  { to: '/measurements', label: 'Ölçümler', icon: Ruler },
  { to: '/profile', label: 'Profil', icon: User },
]

const secondaryItems = [
  { to: '/meal-plan', label: 'Yemek Planı', icon: ChefHat },
  { to: '/creatine', label: 'Kreatin', icon: Pill },
  { to: '/achievements', label: 'Başarılar', icon: Trophy },
  { to: '/export', label: 'Dışa Aktar', icon: Download },
]

export function Sidebar({ open, onClose }: SidebarProps) {
  const location = useLocation()

  const sidebarContent = (
    <aside className="fixed inset-y-0 left-0 z-40 w-64 flex flex-col bg-[#0f0f14] border-r border-white/[0.06]">
      {/* Logo */}
      <div className="flex items-center justify-between px-5 h-16 border-b border-white/[0.06]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-violet-600 flex items-center justify-center">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <span className="text-[15px] font-semibold text-white tracking-tight">FitnessPro</span>
        </div>
        <button
          onClick={onClose}
          className="lg:hidden p-1.5 rounded-md text-white/40 hover:text-white hover:bg-white/[0.06] transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
        <p className="text-[10px] font-semibold text-white/25 uppercase tracking-widest px-3 mb-3">
          Ana Menü
        </p>
        {navItems.map(({ to, label, icon: Icon }) => {
          const isActive = location.pathname === to
          return (
            <NavLink
              key={to}
              to={to}
              onClick={() => { if (window.innerWidth < 1024) onClose() }}
              className={[
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-all duration-150',
                isActive
                  ? 'bg-violet-600/20 text-violet-300 border border-violet-500/20'
                  : 'text-white/50 hover:text-white/90 hover:bg-white/[0.05]',
              ].join(' ')}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-violet-400' : ''}`} />
              {label}
              {isActive && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-violet-400" />
              )}
            </NavLink>
          )
        })}

        <div className="pt-4 mt-2 border-t border-white/[0.06]">
          <p className="text-[10px] font-semibold text-white/25 uppercase tracking-widest px-3 mb-3">
            Araçlar
          </p>
          {secondaryItems.map(({ to, label, icon: Icon }) => {
            const isActive = location.pathname === to
            return (
              <NavLink
                key={to}
                to={to}
                onClick={() => { if (window.innerWidth < 1024) onClose() }}
                className={[
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-150',
                  isActive
                    ? 'bg-violet-600/20 text-violet-300'
                    : 'text-white/35 hover:text-white/70 hover:bg-white/[0.04]',
                ].join(' ')}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                {label}
              </NavLink>
            )
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-white/[0.06]">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[11px] text-white/30">Sistem aktif</span>
        </div>
      </div>
    </aside>
  )

  return (
    <>
      <div className="hidden lg:block">{sidebarContent}</div>
      <div className="lg:hidden">
        <AnimatePresence>
          {open && (
            <>
              <motion.div
                key="overlay"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
                onClick={onClose}
                className="fixed inset-0 z-30 bg-black/60"
              />
              <motion.div
                key="sidebar"
                initial={{ x: '-100%' }}
                animate={{ x: 0 }}
                exit={{ x: '-100%' }}
                transition={{ type: 'tween', duration: 0.2 }}
              >
                {sidebarContent}
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>
    </>
  )
}
