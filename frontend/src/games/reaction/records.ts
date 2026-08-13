import type { BuiltinGameLeaderboardPresentation } from '../../game-platform/types'

export const reactionLeaderboard: BuiltinGameLeaderboardPresentation = {
  description: '按个人历史最佳三轮平均时间排序，数值越低越快。',
  entryDetail: (entry) => `${entry.games} 次测试 · 总平均 ${entry.averageMs} ms`,
  entryScore: (entry) => `${entry.bestMs} ms`,
  note: '排行榜采用完成三轮后的平均反应时间。',
}
