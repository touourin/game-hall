import { beforeEach, describe, expect, it } from 'vitest'
import {
  applyTheme,
  currentTheme,
  DEFAULT_THEME,
  initializeTheme,
  isLightTheme,
  storedTheme,
  THEME_DEFINITIONS,
  THEME_IDS,
  themeColorScheme,
} from './theme'

describe('theme preferences', () => {
  beforeEach(() => {
    document.head.innerHTML = '<meta name="theme-color" content="#000000">'
    applyTheme(DEFAULT_THEME)
    localStorage.clear()
    delete document.documentElement.dataset.theme
    delete document.documentElement.dataset.colorScheme
  })

  it('uses the default theme when no valid preference exists', () => {
    expect(storedTheme()).toBe('amber')

    localStorage.setItem('game-hall:theme', 'unknown')
    expect(storedTheme()).toBe('amber')
  })

  it('keeps theme definitions in the light-dark display order', () => {
    const expectedOrder = ['amber', 'emerald', 'royal', 'midnight']

    expect([...THEME_IDS]).toEqual(expectedOrder)
    expect(THEME_DEFINITIONS.map(({ id }) => id)).toEqual(expectedOrder)
    expect(THEME_DEFINITIONS.map(({ colorScheme }) => colorScheme)).toEqual([
      'light',
      'dark',
      'light',
      'dark',
    ])
  })

  it('persists and applies the selected theme', () => {
    applyTheme('midnight')

    expect(document.documentElement.dataset.theme).toBe('midnight')
    expect(document.documentElement.dataset.colorScheme).toBe('dark')
    expect(document.querySelector('meta[name="theme-color"]')?.getAttribute('content')).toBe('#050607')
    expect(currentTheme.value).toBe('midnight')
    expect(storedTheme()).toBe('midnight')
  })

  it('classifies both light themes without relying on theme ids in components', () => {
    expect(themeColorScheme('emerald')).toBe('dark')
    expect(themeColorScheme('midnight')).toBe('dark')
    expect(isLightTheme('royal')).toBe(true)
    expect(isLightTheme('amber')).toBe(true)

    applyTheme('amber')
    expect(document.documentElement.dataset.colorScheme).toBe('light')
    expect(storedTheme()).toBe('amber')
  })

  it('restores the saved theme during startup', () => {
    localStorage.setItem('game-hall:theme', 'royal')
    initializeTheme()

    expect(document.documentElement.dataset.theme).toBe('royal')
    expect(document.documentElement.dataset.colorScheme).toBe('light')
    expect(document.querySelector('meta[name="theme-color"]')?.getAttribute('content')).toBe('#cbd3d9')
  })

})
