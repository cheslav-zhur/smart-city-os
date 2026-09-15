import { useEffect, useState } from 'react'
import {
  applyTheme,
  persistTheme,
  readStoredTheme,
  type DeskTheme,
} from './theme'

function MoonIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M21 14.5A8.5 8.5 0 0 1 9.5 3a7 7 0 1 0 11.5 11.5Z"
      />
    </svg>
  )
}

function SunIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <circle cx="12" cy="12" r="4" />
      <path
        strokeLinecap="round"
        d="M12 3v1.5M12 19.5V21M4.5 12H3M21 12h-1.5M6.2 6.2 5.1 5.1M18.9 18.9l-1.1-1.1M6.2 17.8l-1.1 1.1M18.9 5.1l-1.1 1.1"
      />
    </svg>
  )
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<DeskTheme>(() => readStoredTheme())

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  function toggle() {
    const next: DeskTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    persistTheme(next)
    applyTheme(next)
  }

  const toLight = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggle}
      className="inline-flex items-center justify-center rounded-xl bg-slate-900/5 p-2.5 text-slate-600 transition hover:bg-slate-900/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500/50 dark:bg-white/5 dark:text-slate-300 dark:hover:bg-white/10"
      aria-label={toLight ? 'Switch to light theme' : 'Switch to dark theme'}
      title={toLight ? 'Light theme' : 'Dark theme'}
    >
      {toLight ? <SunIcon /> : <MoonIcon />}
    </button>
  )
}
