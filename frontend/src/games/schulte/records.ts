import {
  formatMatchDuration,
  formatRecordDuration,
} from '../../game-platform/recordFormatting'
import type {
  BuiltinGameLeaderboardPresentation,
  BuiltinGameStatsPresentation,
} from '../../game-platform/types'

export const schulteLeaderboard: BuiltinGameLeaderboardPresentation = {
  description: '按个人最快完成时间排序，数值越低越快。',
  entryDetail: (entry) =>
    `${entry.games} 次挑战 · 平均 ${formatRecordDuration(entry.averageMs)}`,
  entryScore: (entry) => formatRecordDuration(entry.bestMs),
  note: '排行榜采用服务端计时，并验证 1–25 的完整点击顺序。',
}

export const schulteStats: BuiltinGameStatsPresentation = {
  description: '记录每次 5×5 标准挑战的完成用时与点击准确率。',
  summaryItems: (summary) => [
    { value: summary.games, label: '挑战次数' },
    { value: formatMatchDuration(summary.bestMs), label: '历史最佳' },
    { value: formatMatchDuration(summary.averageMs), label: '平均用时' },
  ],
  historyOutcome: () => '格',
  historyTitle: (match) => `5×5 方格 · ${formatMatchDuration(match.scoreMs)}`,
  historyMeta: (_match, date) => `${date} · 标准挑战`,
  detailSection: (match) => {
    const state = match.details.state
    const mistakes = Number(state?.mistakes ?? 0)
    return {
      title: '舒尔特挑战成绩',
      metrics: [
        {
          status: 'success',
          label: '5×5 标准方格',
          value: formatMatchDuration(state?.elapsed_ms),
          note: '按顺序完成 1–25',
        },
        {
          status: 'success',
          label: '点击准确率',
          value: `${Math.round(25 / (25 + mistakes) * 100)}%`,
          note: `${mistakes} 次错误点击`,
        },
      ],
    }
  },
  detailWinnerLabel: () => '舒尔特挑战完成',
  detailNote: (match) => match.ranked
    ? '本次成绩计入舒尔特方格排行榜'
    : '本次成绩不计排行榜',
}
