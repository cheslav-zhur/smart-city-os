import { useState } from 'react'
import {
  applyTheme,
  persistTheme,
  readStoredTheme,
  type DeskTheme,
} from './theme'

export function ThemeToggle() {
  const [theme, setTheme] = useState<DeskTheme>(() => readStoredTheme())

  function toggle() {
    const next: DeskTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    persistTheme(next)
    applyTheme(next)
  }

  return (
    <button
      type="button"
      onClick={toggle}
      className="rounded-xl bg-slate-900/5 px-3 py-1.5 text-sm font-medium text-slate-600 transition hover:bg-slate-900/10 dark:bg-white/5 dark:text-slate-300 dark:hover:bg-white/10"
      aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
    >
      {theme === 'dark' ? 'Light' : 'Dark'}
    </button>
  )
}
