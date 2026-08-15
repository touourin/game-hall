import { gameRegistration } from './game-platform/registry'
import { THIRD_PARTY_GAME_REGISTRATIONS } from './thirdPartyGameRegistry'

describe('third-party game registrations', () => {
  it('publishes only the three production games from registry.json', () => {
    expect(THIRD_PARTY_GAME_REGISTRATIONS.map(({ key }) => key)).toEqual([
      'plugin-cheat-poker',
      'plugin-crazy-futures',
      'plugin-pyramid-solitaire',
    ])
    expect(gameRegistration('plugin-number-vault')).toBeNull()
    expect(gameRegistration('plugin-star-stones')).toBeNull()
  })

  it('adapts plugin metadata to the shared game registration contract', () => {
    const registration = gameRegistration('plugin-pyramid-solitaire')

    expect(registration).toMatchObject({
      source: 'third_party',
      availability: 'enabled',
      catalog: {
        name: '金字塔纸牌',
        players: { min: 1, max: 1 },
      },
      capabilities: {
        guests: false,
        spectators: true,
        spectatorFrames: false,
        firstPlayer: false,
      },
      presentation: { roomLayout: 'immersive' },
      plugin: { version: '1.0.0' },
      records: { scoreKind: 'time_trial' },
    })
    expect(registration?.rules.defaults).toMatchObject({
      allowSpectators: true,
    })
    expect(registration?.records?.leaderboard?.entryScore({
      rank: 1,
      accountId: 'a1',
      playerName: '玩家一',
      games: 1,
      wins: 1,
      draws: 0,
      winRate: 100,
      bestMs: 65_400,
    })).toBe('1 分 5 秒')
  })
})
