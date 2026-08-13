import { leaderboardPresentation } from './records'

const entry = {
  rank: 1,
  accountId: 'account-1',
  playerName: '玩家',
  games: 12,
  wins: 8,
  draws: 2,
  winRate: 75,
  bestMs: 284,
  averageMs: 320,
  bestScore: 18_600,
  averageScore: 9_300,
}

describe('built-in game record presentations', () => {
  it('uses the shared competitive presentation for ordinary board games', () => {
    const presentation = leaderboardPresentation('gomoku')

    expect(presentation.entryDetail(entry)).toBe('8 胜 · 2 和 / 12 场')
    expect(presentation.entryScore(entry)).toBe('75%')
  })

  it('uses module-owned score formatting for solo games', () => {
    const reaction = leaderboardPresentation('reaction')
    const tetris = leaderboardPresentation('tetris')

    expect(reaction.entryScore(entry)).toBe('284 ms')
    expect(tetris.entryScore(entry)).toBe('18,600 分')
    expect(tetris.titleSuffix?.('timed_180', undefined)).toBe(' · 3 分钟限时')
  })

  it('keeps Avalon mode filters inside the Avalon module', () => {
    const presentation = leaderboardPresentation('avalon')

    expect(presentation.defaultMode).toBe('standard')
    expect(presentation.filters).toHaveLength(3)
    expect(presentation.titleSuffix?.('court_undercurrent', 'shadow_merlin'))
      .toContain('暗影梅林')
  })
})
