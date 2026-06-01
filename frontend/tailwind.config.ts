import type { Config } from 'tailwindcss'

// Tailwind CSS yapılandırması — performans optimizasyonlu
const config: Config = {
  // Dark mode: 'class' stratejisi — HTML kök elementine 'dark' sınıfı eklenerek etkinleştirilir
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        // shadcn/ui renk sistemi — CSS değişkenleri üzerinden tanımlanır
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        // Performans optimizasyonlu animasyonlar
        'fade-in': {
          from: { opacity: '0', transform: 'translate3d(0, 10px, 0)' },
          to: { opacity: '1', transform: 'translate3d(0, 0, 0)' },
        },
        'slide-up': {
          from: { transform: 'translate3d(0, 100%, 0)' },
          to: { transform: 'translate3d(0, 0, 0)' },
        },
        'scale-in': {
          from: { transform: 'scale3d(0.95, 0.95, 1)', opacity: '0' },
          to: { transform: 'scale3d(1, 1, 1)', opacity: '1' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.2s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
        'scale-in': 'scale-in 0.2s ease-out',
      },
    },
  },
  // Performans optimizasyonu - sadece kullanılan sınıfları dahil et
  corePlugins: {
    // Kullanmadığımız özellikleri devre dışı bırak
    preflight: true,
  },
  plugins: [],
}

export default config
