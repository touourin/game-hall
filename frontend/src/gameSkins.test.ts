import {
  GAME_SKINS,
  GAME_SKIN_STORAGE_KEY,
  gameSkinCssVariables,
  gameSkinKind,
  rememberGameSkin,
  storedGameSkin,
  supportsGameSkin,
} from './gameSkins'

describe('game skins', () => {
  beforeEach(() => localStorage.clear())

  it('stores a valid preference and falls back from invalid data', () => {
    expect(storedGameSkin()).toBe('classic-wood')
    rememberGameSkin('midnight-neon')
    expect(storedGameSkin()).toBe('midnight-neon')

    localStorage.setItem(GAME_SKIN_STORAGE_KEY, 'unknown')
    expect(storedGameSkin()).toBe('classic-wood')
  })

  it('provides one beginner, three intermediate, and one advanced skin', () => {
    expect(GAME_SKINS).toHaveLength(5)
    expect(GAME_SKINS.filter((skin) => skin.tier === '初级')).toHaveLength(1)
    expect(GAME_SKINS.filter((skin) => skin.tier === '中级')).toHaveLength(3)
    expect(GAME_SKINS.filter((skin) => skin.tier === '高级')).toHaveLength(1)
  })

  it('only supports multiplayer board and card games', () => {
    expect(gameSkinKind('gomoku')).toBe('board')
    expect(gameSkinKind('poker')).toBe('cards')
    expect(gameSkinKind('hanoi')).toBeNull()
    expect(supportsGameSkin('doudizhu')).toBe(true)
    expect(supportsGameSkin('reaction')).toBe(false)
  })

  it('exposes the selected treatment as shared css variables', () => {
    const css = gameSkinCssVariables('celestial-gold')
    expect(css['--game-board-surface']).toBe('#443251')
    expect(css['--game-card-back-accent']).toBe('#ffe096')
  })
})
