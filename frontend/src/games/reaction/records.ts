import type {
  BuiltinGameLeaderboardPresentation,
  BuiltinGameStatsPresentation,
} from '../../game-platform/types'

export const reactionLeaderboard: BuiltinGameLeaderboardPresentation = {
  description: '按个人历史最佳三轮平均时间排序，数值越低越快。',
  entryDetail: (entry) => `${entry.games} 次测试 · 总平均 ${entry.averageMs} ms`,
  entryScore: (entry) => `${entry.bestMs} ms`,
  note: '排行榜采用完成三轮后的平均反应时间。',
}

export const reactionStats: BuiltinGameStatsPresentation = {
  description: '记录每次三轮测试的平均值与单轮明细。',
  summaryItems: (summary) => [
    { value: summary.games, label: '测试次数' },
    { value: summary.bestMs === null ? '—' : `${summary.bestMs} ms`, label: '历史最佳' },
    { value: summary.averageMs === null ? '—' : `${summary.averageMs} ms`, label: '总平均' },
  ],
  historyOutcome: () => '测',
  historyTitle: (match) => `三轮平均 · ${match.scoreMs} ms`,
  historyMeta: (_match, date) => `${date} · 三轮测试`,
  detailSection: (match) => ({
    title: '反应挑战成绩',
    metrics: (match.details.state?.results_ms ?? []).map((result, index) => ({
      status: 'success',
      label: `第 ${index + 1} 轮`,
      value: `${result} ms`,
    })),
  }),
  detailWinnerLabel: () => '三轮测试完成',
  detailNote: (match) => match.ranked
    ? '本次成绩计入反应时间排行榜'
    : '本次成绩不计排行榜',
}
