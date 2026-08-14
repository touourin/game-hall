import { builtinGameDefinition, BUILTIN_GAME_DEFINITIONS } from './registry'
import { GAME_CATALOG } from '../gameCatalog'

describe('built-in game registry', () => {
  it('owns the complete board-game integration metadata', () => {
    const definition = builtinGameDefinition('chess')

    expect(BUILTIN_GAME_DEFINITIONS).toHaveLength(18)
    expect(definition?.catalog).toMatchObject({
      order: 50,
      name: '国际象棋',
      players: { min: 2, max: 2 },
      tone: 'chess',
      category: '棋类竞技',
    })
    expect(definition?.catalog.artwork).toContain('chess')
    expect(definition?.presentation.roomLayout).toBe('standard')
    expect(definition?.presentation.skinKind).toBe('board')
    expect(definition?.capabilities).toMatchObject({
      undo: true,
      draw: true,
      spectators: true,
      replay: true,
      ai: false,
    })
    expect(definition?.rules.defaults).toEqual({
      firstPlayer: 'random',
      allowGuests: true,
      allowSpectators: true,
      allowUndo: true,
      allowDraw: true,
    })
  })

  it('owns each migrated board game and ignores third-party ids', () => {
    expect(builtinGameDefinition('gomoku')?.presentation.skinKind).toBe('board')
    expect(builtinGameDefinition('xiangqi')?.capabilities.ai).toBe(true)
    expect(builtinGameDefinition('go')?.capabilities.ai).toBe(true)
    expect(builtinGameDefinition('junqi')?.presentation.roomLayout).toBe('wide')
    expect(builtinGameDefinition('plugin-number-vault')).toBeNull()
  })

  it('keeps the migrated game in its existing hall position without duplicates', () => {
    const keys = GAME_CATALOG.map((game) => game.key)

    expect(new Set(keys).size).toBe(keys.length)
    expect(keys.filter((key) => key === 'chess')).toHaveLength(1)
    expect(keys.indexOf('xiangqi')).toBeLessThan(keys.indexOf('chess'))
    expect(keys.indexOf('chess')).toBeLessThan(keys.indexOf('go'))
  })

  it('lets every built-in solo game own its launcher presentation', () => {
    const soloDefinitions = BUILTIN_GAME_DEFINITIONS.filter(
      (definition) => definition.catalog.players.max === 1,
    )

    expect(soloDefinitions).toHaveLength(7)
    for (const definition of soloDefinitions) {
      expect(definition.presentation.solo).toBeDefined()
      expect(definition.presentation.solo?.content({}).metrics).toHaveLength(3)
    }

    expect(
      builtinGameDefinition('minesweeper')?.records?.modeFromRules?.({
        difficulty: 'expert',
      }),
    ).toBe('expert')
    expect(
      builtinGameDefinition('tetris')?.records?.modeFromRules?.({
        challengeMode: 'timed',
        durationSeconds: 300,
      }),
    ).toBe('timed_300')
  })
})
