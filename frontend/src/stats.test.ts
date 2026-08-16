import { loadLeaderboard } from './stats'

vi.mock('./access', () => ({ storedAccessToken: () => 'access-token' }))
vi.mock('./account', () => ({ storedAccountToken: () => 'account-token' }))

describe('stats API boundary', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('normalizes score fields omitted by another leaderboard kind', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      ok: true,
      players: [{
        rank: 1,
        accountId: 'account-1',
        playerName: '玩家一号',
        games: 3,
        wins: 2,
        draws: 0,
        winRate: 66.7,
      }],
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }))

    const [entry] = await loadLeaderboard('gomoku')

    expect(entry).toMatchObject({
      bestMs: null,
      averageMs: null,
      bestScore: null,
      averageScore: null,
    })
  })
})
