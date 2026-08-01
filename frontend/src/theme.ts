export type ThemeName = 'emerald' | 'midnight' | 'royal'

const THEME_KEY = 'game-hall:theme'
const LEGACY_THEME_KEY = 'avalon:theme'
const THEMES: ThemeName[] = ['emerald', 'midnight', 'royal']

export function storedTheme(): ThemeName {
  const saved = localStorage.getItem(THEME_KEY)
  if (THEMES.includes(saved as ThemeName)) return saved as ThemeName

  const legacyTheme = localStorage.getItem(LEGACY_THEME_KEY)
  const migratedTheme = legacyTheme === 'avalon' ? 'emerald' : legacyTheme
  if (THEMES.includes(migratedTheme as ThemeName)) {
    localStorage.setItem(THEME_KEY, migratedTheme as ThemeName)
    localStorage.removeItem(LEGACY_THEME_KEY)
    return migratedTheme as ThemeName
  }

  return 'emerald'
}

export function applyTheme(theme: ThemeName): void {
  document.documentElement.dataset.theme = theme
  localStorage.setItem(THEME_KEY, theme)
  localStorage.removeItem(LEGACY_THEME_KEY)
}

export function initializeTheme(): void {
  applyTheme(storedTheme())
}
