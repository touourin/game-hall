import { formatMatchDuration } from '../../game-platform/recordFormatting'
import type {
  BuiltinGameLeaderboardPresentation,
  BuiltinGameStatsPresentation,
} from '../../game-platform/types'

export const hanoiLeaderboard: BuiltinGameLeaderboardPresentation = {
  description: '按累计通关次数排序，同次数时优先更早完成挑战的玩家。',
  entryDetail: (entry) => `${entry.games} 次挑战 · ${entry.wins} 次通关`,
  entryScore: (entry) => `${entry.wins} 次`,
  note: '不同层数都会累计为一次有效通关，详细步数和时间保存在个人战绩中。',
}

export const hanoiStats: BuiltinGameStatsPresentation = {
  description: '记录每次通关的层数、步数与完成用时。',
  summaryItems: (summary) => [
    { value: summary.games, label: '挑战次数' },
    { value: summary.wins, label: '完成次数' },
    { value: `${summary.winRate}%`, label: '完成率' },
  ],
  historyOutcome: () => '成',
  historyTitle: (match) => match.reason,
  historyMeta: (_match, date) => `${date} · 单人益智挑战`,
  detailSection: (match) => {
    const state = match.details.state
    const discCount = Number(state?.disc_count ?? 0)
    return {
      title: '汉诺塔挑战成绩',
      metrics: [
        {
          status: 'success',
          label: `${discCount} 层圆盘`,
          value: `${state?.moves ?? 0} 步完成`,
          note: `理论最少 ${2 ** discCount - 1} 步`,
        },
        {
          status: 'success',
          label: '完成用时',
          value: formatMatchDuration(state?.elapsed_ms),
        },
      ],
    }
  },
  detailWinnerLabel: () => '汉诺塔挑战完成',
  detailNote: (match) => match.ranked
    ? '本次通关计入汉诺塔累计通关榜'
    : '本次通关不计排行榜',
}
