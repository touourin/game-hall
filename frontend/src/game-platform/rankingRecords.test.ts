import { createScoredGameRecords } from './recordFormatting'
import type { LeaderboardEntry, MatchDetail, MatchHistoryItem, StatsSummary } from '../stats'

describe('ranking points presentations', () => {
  const records = createScoredGameRecords('ranking', '名次测试')

  it('formats positive, zero, and negative totals without treating negatives as missing', () => {
    for (const [totalPoints, expected] of [[2, '+2 分'], [0, '0 分'], [-1, '-1 分']] as const) {
      expect(records.leaderboard!.entryScore({ totalPoints } as LeaderboardEntry)).toBe(expected)
    }
    expect(records.leaderboard!.entryScore({ totalPoints: Number.NaN } as LeaderboardEntry)).toBe('—')
    expect(records.leaderboard!.entryScore({} as LeaderboardEntry)).toBe('—')
    expect(records.stats!.summaryItems({ games: 2, wins: 0, totalPoints: -2 } as StatsSummary))
      .toContainEqual({ value: '-2 分', label: '累计积分' })
  })

  it('shows placement and exact points in personal history and match details', () => {
    expect(records.stats!.historyTitle({ role: '第 4 名', scoreValue: -1 } as MatchHistoryItem))
      .toBe('名次测试 · 第 4 名 · -1 分')
    const match = { details: { players: [
      { id: 'a', name: '甲', role: '第 3 名', scoreValue: 0 },
      { id: 'b', name: '乙', role: '第 4 名', scoreValue: -1 },
    ] } } as MatchDetail
    expect(records.stats!.detailSection!(match).metrics).toEqual([
      { status: 'success', label: '甲 · 第 3 名', value: '0 分' },
      { status: 'failed', label: '乙 · 第 4 名', value: '-1 分' },
    ])
  })
})
