import { readonly, ref } from 'vue'

export const THEME_IDS = ['emerald', 'midnight', 'royal', 'amber'] as const

export type ThemeName = typeof THEME_IDS[number]
export type ThemeColorScheme = 'dark' | 'light'

export interface ThemeDefinition {
  id: ThemeName
  name: string
  description: string
  colors: readonly [string, string, string]
  colorScheme: ThemeColorScheme
}

export const THEME_DEFINITIONS = [
  {
    id: 'emerald',
    name: '极光雾舱',
    description: '深海军蓝、冷银玻璃与克制冰蓝仪表光',
    colors: ['#020810', '#0d1d2e', '#64c6ea'],
    colorScheme: 'dark',
  },
  {
    id: 'midnight',
    name: '曜石黑钛',
    description: '曜石黑陶瓷、石墨烟玻璃与冷银钛光',
    colors: ['#050607', '#1c2227', '#8ea9b8'],
    colorScheme: 'dark',
  },
  {
    id: 'royal',
    name: '月白陶瓷',
    description: '冷月灰陶瓷、乳雾玻璃与自然铝',
    colors: ['#cbd3d9', '#f4f2ec', '#4d8b7b'],
    colorScheme: 'light',
  },
  {
    id: 'amber',
    name: '橙釉象牙',
    description: '象牙白陶瓷、柔杏雾光与橙釉强调',
    colors: ['#f0e6da', '#fff9f1', '#c45124'],
    colorScheme: 'light',
  },
] as const satisfies readonly ThemeDefinition[]

const THEME_KEY = 'game-hall:theme'
const activeTheme = ref<ThemeName>('royal')

export const currentTheme = readonly(activeTheme)

export function storedTheme(): ThemeName {
  const saved = localStorage.getItem(THEME_KEY)
  if (THEME_IDS.includes(saved as ThemeName)) return saved as ThemeName

  return 'royal'
}

export function themeColorScheme(theme: ThemeName): ThemeColorScheme {
  return THEME_DEFINITIONS.find((definition) => definition.id === theme)!
    .colorScheme
}

export function isLightTheme(theme: ThemeName): boolean {
  return themeColorScheme(theme) === 'light'
}

export function applyTheme(theme: ThemeName): void {
  activeTheme.value = theme
  document.documentElement.dataset.theme = theme
  document.documentElement.dataset.colorScheme = themeColorScheme(theme)
  localStorage.setItem(THEME_KEY, theme)
}

export function initializeTheme(): void {
  applyTheme(storedTheme())
}
