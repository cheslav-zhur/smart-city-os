export type DeskTheme = 'dark' | 'light'

export const THEME_STORAGE_KEY = 'desk-theme'

export function readStoredTheme(): DeskTheme {
  try {
    const value = localStorage.getItem(THEME_STORAGE_KEY)
    if (value === 'light' || value === 'dark') {
      return value
    }
  } catch {
    // Private mode / blocked storage — fall through to default.
  }
  return 'dark'
}

export function applyTheme(theme: DeskTheme): void {
  document.documentElement.classList.toggle('dark', theme === 'dark')
}

export function persistTheme(theme: DeskTheme): void {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  } catch {
    // Ignore quota / private mode.
  }
}
