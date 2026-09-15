/** Console color scheme (class strategy on <html>). */
export type DeskTheme = 'dark' | 'light'

export const THEME_STORAGE_KEY = 'desk-theme'
export const DEFAULT_THEME: DeskTheme = 'dark'

export function isDeskTheme(value: string): value is DeskTheme {
  return value === 'dark' || value === 'light'
}

export function oppositeTheme(theme: DeskTheme): DeskTheme {
  return theme === 'dark' ? 'light' : 'dark'
}

export function readStoredTheme(): DeskTheme {
  try {
    const value = localStorage.getItem(THEME_STORAGE_KEY)
    if (value != null && isDeskTheme(value)) {
      return value
    }
  } catch {
    // Private mode / blocked storage — fall through to default.
  }
  return DEFAULT_THEME
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
