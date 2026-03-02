import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#09090b',
        sidebar: '#111113',
        card: '#18181b',
        'card-hover': '#1f1f23',
        border: '#27272a',
        input: '#1c1c1f',
        primary: {
          DEFAULT: '#22c55e',
          dark: '#16a34a',
          light: '#4ade80',
          subtle: 'rgba(34,197,94,0.12)',
        },
        muted: {
          DEFAULT: '#a1a1aa',
          dark: '#71717a',
        },
        danger: {
          DEFAULT: '#ef4444',
          dark: '#dc2626',
          subtle: 'rgba(239,68,68,0.12)',
        },
        warning: {
          DEFAULT: '#f59e0b',
          subtle: 'rgba(245,158,11,0.12)',
        },
        info: {
          DEFAULT: '#3b82f6',
          subtle: 'rgba(59,130,246,0.12)',
        },
        purple: {
          DEFAULT: '#a855f7',
          subtle: 'rgba(168,85,247,0.12)',
        },
      },
      fontFamily: {
        sans: ['Segoe UI', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-in': 'slideIn 0.2s ease-out',
        'spin-slow': 'spin 1.5s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
