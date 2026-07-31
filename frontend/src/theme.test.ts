import { beforeEach, describe, expect, it } from 'vitest'
import { applyTheme, initializeTheme, storedTheme } from './theme'

describe('theme preferences', () => {
  beforeEach(() => {
    localStorage.clear()
    delete document.documentElement.dataset.theme
  })

  it('uses the default theme when no valid preference exists', () => {
    expect(storedTheme()).toBe('avalon')

    localStorage.setItem('avalon:theme', 'unknown')
    expect(storedTheme()).toBe('avalon')
  })

  it('persists and applies the selected theme', () => {
    applyTheme('midnight')

    expect(document.documentElement.dataset.theme).toBe('midnight')
    expect(storedTheme()).toBe('midnight')
  })

  it('restores the saved theme during startup', () => {
    localStorage.setItem('avalon:theme', 'royal')
    initializeTheme()

    expect(document.documentElement.dataset.theme).toBe('royal')
  })
})
