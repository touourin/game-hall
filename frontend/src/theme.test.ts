import { beforeEach, describe, expect, it } from 'vitest'
import {
  applyTheme,
  currentTheme,
  initializeTheme,
  isLightTheme,
  storedTheme,
  themeColorScheme,
} from './theme'

describe('theme preferences', () => {
  beforeEach(() => {
    applyTheme('royal')
    localStorage.clear()
    delete document.documentElement.dataset.theme
    delete document.documentElement.dataset.colorScheme
  })

  it('uses the default theme when no valid preference exists', () => {
    expect(storedTheme()).toBe('royal')

    localStorage.setItem('game-hall:theme', 'unknown')
    expect(storedTheme()).toBe('royal')
  })

  it('persists and applies the selected theme', () => {
    applyTheme('midnight')

    expect(document.documentElement.dataset.theme).toBe('midnight')
    expect(document.documentElement.dataset.colorScheme).toBe('dark')
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
  })

})
