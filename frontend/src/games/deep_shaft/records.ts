import type {
  BuiltinGameLeaderboardPresentation,
  BuiltinGameStatsPresentation,
} from '../../game-platform/types'

export const deepShaftLeaderboard: BuiltinGameLeaderboardPresentation = {
  description: '按个人历史最深层数排序，抵达层数越深排名越前。',
  entryDetail: (entry) =>
    `${entry.games} 次挑战 · 平均 ${entry.averageScore?.toLocaleString()} 层`,
  entryScore: (entry) => `${entry.bestScore?.toLocaleString()} 层`,
  note: '服务器会根据随机种子重放全部左右输入，再保存实际抵达的最深层数。',
}

export const deepShaftStats: BuiltinGameStatsPresentation = {
  description: '记录每次深井探索的最深层数、剩余生命和挑战用时。',
  summaryItems: (summary) => [
    { value: summary.games, label: '挑战次数' },
    { value: summary.bestScore?.toLocaleString() ?? '—', label: '历史最深层数' },
    { value: summary.averageScore?.toLocaleString() ?? '—', label: '平均抵达层数' },
  ],
  historyOutcome: () => '层',
  historyTitle: (match) => `最深抵达 · ${match.scoreValue?.toLocaleString()} 层`,
  historyMeta: (match, date) => `${date} · ${match.reason}`,
  detailWinnerLabel: (match) => match.winner === 'completed'
    ? '百层深井通关'
    : '深井探索结束',
  detailNote: (match) => match.ranked
    ? '本轮最深层数计入百层深井排行榜'
    : '本轮成绩不计排行榜',
}
