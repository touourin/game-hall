export type ThemeName = 'avalon' | 'midnight' | 'royal'

const THEME_KEY = 'avalon:theme'
const THEMES: ThemeName[] = ['avalon', 'midnight', 'royal']

export function storedTheme(): ThemeName {
  const saved = localStorage.getItem(THEME_KEY)
  return THEMES.includes(saved as ThemeName) ? (saved as ThemeName) : 'avalon'
}

export function applyTheme(theme: ThemeName): void {
  document.documentElement.dataset.theme = theme
  localStorage.setItem(THEME_KEY, theme)
}

export function initializeTheme(): void {
  applyTheme(storedTheme())
}
