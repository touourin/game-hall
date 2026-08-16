import { readonly, ref } from 'vue'

export type ThemeColorScheme = 'dark' | 'light'

export interface ThemeDefinition<Id extends string = string> {
  id: Id
  name: string
  description: string
  colors: readonly [background: string, surface: string, accent: string]
  colorScheme: ThemeColorScheme
}

export const THEME_DEFINITIONS = [
  {
    id: 'amber',
    name: '橘光晴釉',
    description: '奶油暖杏、柔白陶面与鲜润橘釉',
    colors: ['#f8e4cc', '#fffaf2', '#f26a13'],
    colorScheme: 'light',
  },
  {
    id: 'emerald',
    name: '幽蓝冷钢',
    description: '近黑军蓝、深蓝钢面与冰蓝辉光',
    colors: ['#020810', '#0d1d2e', '#64c6ea'],
    colorScheme: 'dark',
  },
  {
    id: 'royal',
    name: '月白云瓷',
    description: '月白冷灰、柔白云瓷与灰绿釉面',
    colors: ['#cbd3d9', '#f4f2ec', '#4d8b7b'],
    colorScheme: 'light',
  },
  {
    id: 'midnight',
    name: '曜石黑钛',
    description: '曜石黑陶、石墨烟面与冷银钛光',
    colors: ['#050607', '#1c2227', '#8ea9b8'],
    colorScheme: 'dark',
  },
] as const satisfies readonly ThemeDefinition[]

export type ThemeName = typeof THEME_DEFINITIONS[number]['id']
export const THEME_IDS = Object.freeze(
  THEME_DEFINITIONS.map(({ id }) => id),
)
export const DEFAULT_THEME: ThemeName = THEME_DEFINITIONS[0].id

const THEME_KEY = 'game-hall:theme'
const activeTheme = ref<ThemeName>(DEFAULT_THEME)

export const currentTheme = readonly(activeTheme)

export function storedTheme(): ThemeName {
  const saved = localStorage.getItem(THEME_KEY)
  if (THEME_IDS.includes(saved as ThemeName)) return saved as ThemeName

  return DEFAULT_THEME
}

export function themeColorScheme(theme: ThemeName): ThemeColorScheme {
  return themeDefinition(theme).colorScheme
}

export function isLightTheme(theme: ThemeName): boolean {
  return themeColorScheme(theme) === 'light'
}

export function applyTheme(theme: ThemeName): void {
  const definition = themeDefinition(theme)
  activeTheme.value = theme
  document.documentElement.dataset.theme = theme
  document.documentElement.dataset.colorScheme = definition.colorScheme
  document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')
    ?.setAttribute('content', definition.colors[0])
  localStorage.setItem(THEME_KEY, theme)
}

export function initializeTheme(): void {
  applyTheme(storedTheme())
}

function themeDefinition(theme: ThemeName): ThemeDefinition<ThemeName> {
  return THEME_DEFINITIONS.find((definition) => definition.id === theme)!
}
