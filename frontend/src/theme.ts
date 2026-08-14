import { readonly, ref } from 'vue'

export type ThemeName = 'emerald' | 'midnight' | 'royal'

const THEME_KEY = 'game-hall:theme'
const THEMES: ThemeName[] = ['emerald', 'midnight', 'royal']
const activeTheme = ref<ThemeName>('royal')

export const currentTheme = readonly(activeTheme)

export function storedTheme(): ThemeName {
  const saved = localStorage.getItem(THEME_KEY)
  if (THEMES.includes(saved as ThemeName)) return saved as ThemeName

  return 'royal'
}

export function applyTheme(theme: ThemeName): void {
  activeTheme.value = theme
  document.documentElement.dataset.theme = theme
  localStorage.setItem(THEME_KEY, theme)
}

export function initializeTheme(): void {
  applyTheme(storedTheme())
}
