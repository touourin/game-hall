import {
  formatMatchDuration,
  formatRecordNumber,
} from '../../game-platform/recordFormatting'
import type {
  BuiltinGameLeaderboardPresentation,
  BuiltinGameStatsPresentation,
} from '../../game-platform/types'

export const deepShaftLeaderboard: BuiltinGameLeaderboardPresentation = {
  description: '按个人历史最深层数排序，抵达层数越深排名越前。',
  entryDetail: (entry) =>
    `${entry.games} 次挑战 · 平均 ${formatRecordNumber(entry.averageScore, '层')}`,
  entryScore: (entry) => formatRecordNumber(entry.bestScore, '层'),
  note: '服务器会根据随机种子重放全部左右输入，再保存实际抵达的最深层数。',
}

export const deepShaftStats: BuiltinGameStatsPresentation = {
  description: '记录每次深井探索的最深层数、剩余生命和挑战用时。',
  summaryItems: (summary) => [
    { value: summary.games, label: '挑战次数' },
    { value: formatRecordNumber(summary.bestScore), label: '历史最深层数' },
    { value: formatRecordNumber(summary.averageScore), label: '平均抵达层数' },
  ],
  historyOutcome: () => '层',
  historyTitle: (match) => `最深抵达 · ${formatRecordNumber(match.scoreValue, '层')}`,
  historyMeta: (match, date) => `${date} · ${match.reason}`,
  detailSection: (match) => {
    const state = match.details.state
    return {
      title: '百层深井挑战成绩',
      metrics: [
        {
          status: match.winner === 'completed' ? 'success' : 'failed',
          label: match.winner === 'completed'
            ? '抵达第一百层'
            : `最深抵达第 ${state?.deepest_floor ?? 0} 层`,
          value: formatMatchDuration(state?.elapsed_ms),
          note: `结束时剩余 ${state?.health ?? 0} 点生命`,
        },
        {
          status: 'success',
          label: '服务端轨迹校验',
          value: `${state?.input_count ?? 0} 帧输入`,
          note: '固定 60 Hz 重建平台、移动与碰撞',
        },
      ],
    }
  },
  detailWinnerLabel: (match) => match.winner === 'completed'
    ? '百层深井通关'
    : '深井探索结束',
  detailNote: (match) => match.ranked
    ? '本轮最深层数计入百层深井排行榜'
    : '本轮成绩不计排行榜',
}
