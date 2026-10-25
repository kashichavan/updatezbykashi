import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#070b14',
        foreground: '#f1f5f9',
        card: '#0d1527',
        card_hover: '#141c2e',
        border: '#1e293b',
        border_subtle: '#0f172a',
        accent: '#38bdf8',
        accent_soft: 'rgba(56, 189, 248, 0.15)',
        accent_glow: 'rgba(56, 189, 248, 0.25)',
        emerald: '#10b981', // Aligning with --success
        emerald_soft: 'rgba(16, 185, 129, 0.1)',
        rose: '#ef4444', // Aligning with --danger
        amber: '#f59e0b', // Aligning with --warning
        indigo: '#4f46e5',
        muted: '#64748b',
        subtle: '#0f172a',
        muted_soft: 'rgba(100, 116, 139, 0.3)',
        gold: '#d97706',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
    screens: {
      xs: '320px',
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
      '2xl': '1536px',
    },
  },
  plugins: [
    function ({ addUtilities }: { addUtilities: any }) {
      const newUtilities = {
        '.glass-panel': {
          background: 'rgba(18, 24, 38, 0.6)',
          backdropFilter: 'blur(16px) saturate(180%)',
          '-webkit-backdrop-filter': 'blur(16px) saturate(180%)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        },
        '.glass-card-hover': {
          transition: 'transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease, border-color 0.25s ease',
        },
        '.glass-card-hover:hover': {
          transform: 'translateY(-4px)',
          borderColor: 'rgba(56, 189, 248, 0.4)',
          boxShadow: '0 12px 24px -8px rgba(56, 189, 248, 0.25)',
        },
        '.status-badge': {
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '2px 8px',
        borderRadius: '9999px',
        fontSize: '0.75rem',
        fontWeight: '600',
        },
        '.status-badge .status-dot': {
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          flexShrink: '0',
        },
        '.interactive-element': {
          transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        },
        '.skeleton': {
          background: 'linear-gradient(90deg, var(--surface-card) 25%, var(--surface-hover) 50%, var(--surface-card) 75%)',
          backgroundSize: '200% 100%',
          animation: 'shimmer 1.5s infinite',
          borderRadius: '6px',
        },
      };
      addUtilities(newUtilities, ['responsive', 'hover']);
    },
  ],
};
export default config;
