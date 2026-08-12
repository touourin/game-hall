import { beforeEach, describe, expect, it } from 'vitest'
import { applyTheme, initializeTheme, storedTheme } from './theme'

describe('theme preferences', () => {
  beforeEach(() => {
    localStorage.clear()
    delete document.documentElement.dataset.theme
  })

  it('uses the default theme when no valid preference exists', () => {
    expect(storedTheme()).toBe('royal')

    localStorage.setItem('game-hall:theme', 'unknown')
    expect(storedTheme()).toBe('royal')
  })

  it('persists and applies the selected theme', () => {
    applyTheme('midnight')

    expect(document.documentElement.dataset.theme).toBe('midnight')
    expect(storedTheme()).toBe('midnight')
  })

  it('restores the saved theme during startup', () => {
    localStorage.setItem('game-hall:theme', 'royal')
    initializeTheme()

    expect(document.documentElement.dataset.theme).toBe('royal')
  })

  it('migrates the legacy Avalon theme preference', () => {
    localStorage.setItem('avalon:theme', 'avalon')

    expect(storedTheme()).toBe('emerald')
    expect(localStorage.getItem('game-hall:theme')).toBe('emerald')
    expect(localStorage.getItem('avalon:theme')).toBeNull()
  })
})
