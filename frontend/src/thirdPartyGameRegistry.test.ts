import { gameRegistration } from './game-platform/registry'
import { THIRD_PARTY_GAME_REGISTRATIONS } from './thirdPartyGameRegistry'

describe('third-party game registrations', () => {
  it('publishes every enabled game from registry.json in registry order', () => {
    expect(THIRD_PARTY_GAME_REGISTRATIONS.map(({ key }) => key)).toEqual([
      'plugin-cheat-poker',
      'plugin-crazy-futures',
      'plugin-pyramid-solitaire',
      'plugin-number-vault',
      'plugin-star-stones',
    ])
    expect(gameRegistration('plugin-number-vault')).toMatchObject({
      source: 'third_party',
      availability: 'enabled',
      catalog: { name: '数字密匣' },
      records: { scoreKind: 'outcome' },
    })
    expect(gameRegistration('plugin-star-stones')).toMatchObject({
      source: 'third_party',
      availability: 'enabled',
      catalog: { name: '星石争夺' },
      records: { scoreKind: 'outcome' },
    })
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
