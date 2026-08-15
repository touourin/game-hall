import { gameRegistration, BUILTIN_GAME_REGISTRATIONS } from './registry'
import { GAME_CATALOG } from '../gameCatalog'

describe('built-in game registry', () => {
  it('owns the complete board-game integration metadata', () => {
    const definition = gameRegistration('chess')

    expect(BUILTIN_GAME_REGISTRATIONS).toHaveLength(19)
    expect(definition?.catalog).toMatchObject({
      order: 50,
      name: '国际象棋',
      players: { min: 2, max: 2 },
      tone: 'chess',
      category: '棋类竞技',
    })
    expect(definition?.catalog.artwork).toEqual({
      dark: expect.stringContaining('chess-dark'),
      light: expect.stringContaining('chess-light'),
    })
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

  it('owns each migrated board game and resolves third-party ids', () => {
    expect(gameRegistration('gomoku')?.presentation.skinKind).toBe('board')
    expect(gameRegistration('junqi')?.presentation.roomLayout).toBe('wide')
    expect(gameRegistration('junqi')?.records?.matchDetailComponent).toBeUndefined()
    expect(gameRegistration('plugin-number-vault')?.source).toBe('third_party')
  })

  it('requires every official game to provide both material variants', () => {
    for (const definition of BUILTIN_GAME_REGISTRATIONS) {
      expect(definition.catalog.artwork!.dark).toContain('-dark')
      expect(definition.catalog.artwork!.light).toContain('-light')
      expect(definition.catalog.artwork!.dark).not.toBe(definition.catalog.artwork!.light)
    }
  })

  it('preserves every board-duel capability after sharing defaults', () => {
    const shared = {
      undo: true,
      draw: true,
      guests: true,
      spectators: true,
      spectatorFrames: false,
      firstPlayer: true,
      replay: false,
      ai: false,
    }

    expect(gameRegistration('chess')?.capabilities).toEqual({
      ...shared,
      replay: true,
    })
    expect(gameRegistration('go')?.capabilities).toEqual({
      ...shared,
      ai: true,
    })
    expect(gameRegistration('gomoku')?.capabilities).toEqual(shared)
    expect(gameRegistration('junqi')?.capabilities).toEqual({
      ...shared,
      undo: false,
      draw: false,
    })
    expect(gameRegistration('xiangqi')?.capabilities).toEqual({
      ...shared,
      replay: true,
      ai: true,
    })
  })

  it('preserves every social-table capability after sharing defaults', () => {
    const socialTableKeys = [
      'avalon',
      'departed_suspicion',
      'one_night_werewolf',
      'poker',
      'doudizhu',
      'monopoly',
      'pixel_push',
    ] as const
    const shared = {
      undo: false,
      draw: false,
      guests: true,
      spectators: true,
      spectatorFrames: false,
      firstPlayer: true,
      replay: false,
      ai: false,
    }

    expect(gameRegistration('departed_suspicion')?.capabilities).toEqual(shared)
    expect(gameRegistration('doudizhu')?.capabilities).toEqual(shared)
    expect(gameRegistration('monopoly')?.capabilities).toEqual(shared)
    expect(gameRegistration('pixel_push')?.capabilities).toEqual({
      ...shared,
      firstPlayer: false,
    })
    expect(gameRegistration('poker')?.capabilities).toEqual({
      ...shared,
      firstPlayer: false,
    })
    expect(gameRegistration('one_night_werewolf')?.capabilities).toEqual({
      ...shared,
      firstPlayer: false,
    })
    expect(gameRegistration('avalon')?.capabilities).toEqual({
      ...shared,
      firstPlayer: false,
      replay: true,
      ai: true,
    })

    for (const gameKey of socialTableKeys) {
      const definition = gameRegistration(gameKey)
      const defaults = definition?.rules.defaults ?? {}

      expect('firstPlayer' in defaults).toBe(definition?.capabilities.firstPlayer)
      expect(defaults.allowGuests).toBe(definition?.capabilities.guests)
      expect(defaults.allowSpectators).toBe(definition?.capabilities.spectators)
    }
  })

  it('keeps the migrated game in its existing hall position without duplicates', () => {
    const keys = GAME_CATALOG.map((game) => game.key)

    expect(new Set(keys).size).toBe(keys.length)
    expect(keys.filter((key) => key === 'chess')).toHaveLength(1)
    expect(keys.indexOf('xiangqi')).toBeLessThan(keys.indexOf('chess'))
    expect(keys.indexOf('chess')).toBeLessThan(keys.indexOf('go'))
  })

  it('lets every built-in solo game own its launcher presentation', () => {
    const soloDefinitions = BUILTIN_GAME_REGISTRATIONS.filter(
      (definition) => definition.catalog.players.max === 1,
    )

    expect(soloDefinitions).toHaveLength(7)
    for (const definition of soloDefinitions) {
      expect(definition.presentation.solo).toBeDefined()
      expect(definition.presentation.solo?.content({}).metrics).toHaveLength(3)
      expect(definition.records?.stats?.detailSection).toBeTypeOf('function')
      expect(definition.records?.matchDetailComponent).toBeUndefined()
      expect(definition.capabilities).toMatchObject({
        undo: false,
        draw: false,
        guests: false,
        spectators: true,
        firstPlayer: false,
        replay: false,
        ai: false,
      })
    }

    expect(
      gameRegistration('critical_crossing')?.records?.modeFromRules?.({
        difficulty: '10s',
      }),
    ).toBe('10s')
    expect(
      gameRegistration('minesweeper')?.records?.modeFromRules?.({
        difficulty: 'expert',
      }),
    ).toBe('expert')
    expect(
      gameRegistration('tetris')?.records?.modeFromRules?.({
        challengeMode: 'timed',
        durationSeconds: 300,
      }),
    ).toBe('timed_300')
  })

  it('lets every built-in multiplayer game own its launcher identity', () => {
    const multiplayerDefinitions = BUILTIN_GAME_REGISTRATIONS.filter(
      (definition) => definition.catalog.players.max > 1,
    )

    expect(multiplayerDefinitions).toHaveLength(12)
    for (const definition of multiplayerDefinitions) {
      expect(definition.presentation.launcher).toMatchObject({
        kicker: expect.any(String),
        title: expect.any(String),
        description: expect.any(String),
        accent: expect.stringMatching(/^#[0-9a-f]{6}$/i),
        glow: expect.stringMatching(/^#[0-9a-f]{6}$/i),
      })
    }
  })

  it('lets game modules extend the shared room shell without central branches', () => {
    const avalonRoomShell = gameRegistration('avalon')?.presentation.roomShell
    const oneNightRoomShell = gameRegistration('one_night_werewolf')
      ?.presentation.roomShell

    expect(avalonRoomShell).toMatchObject({
      headerDetailsComponent: expect.any(Object),
      headerActionsComponent: expect.any(Object),
      lobbyComponent: expect.any(Object),
      waitingMessage: expect.any(Function),
      handlesResult: true,
    })
    expect(oneNightRoomShell).toMatchObject({
      headerActionsComponent: expect.any(Object),
      ruleActionsComponent: expect.any(Object),
    })
  })
})
