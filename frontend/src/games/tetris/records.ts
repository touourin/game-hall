import {
  formatMatchDuration,
  formatRecordNumber,
  tetrisRecordModeLabel,
} from '../../game-platform/recordFormatting'
import type {
  BuiltinGameLeaderboardPresentation,
  BuiltinGameStatsPresentation,
} from '../../game-platform/types'

const tetrisRecordFilters = [
  { label: '1 分钟', mode: 'timed_60' },
  { label: '3 分钟', mode: 'timed_180' },
  { label: '5 分钟', mode: 'timed_300' },
  { label: '无限挑战', mode: 'standard' },
] as const

export const tetrisLeaderboard: BuiltinGameLeaderboardPresentation = {
  defaultMode: 'timed_180',
  titleSuffix: (mode) => ` · ${tetrisRecordModeLabel(mode)}`,
  description: '按个人历史最高得分排序，分数越高排名越前。',
  filters: tetrisRecordFilters,
  entryDetail: (entry) =>
    `${entry.games} 次挑战 · 平均 ${formatRecordNumber(entry.averageScore, '分')}`,
  entryScore: (entry) => formatRecordNumber(entry.bestScore, '分'),
  note: '每轮结束后保存最终得分；最高分优先，总平均分用于同分参考。',
}

export const tetrisStats: BuiltinGameStatsPresentation = {
  defaultMode: tetrisLeaderboard.defaultMode,
  titleSuffix: (mode) => ` · ${tetrisRecordModeLabel(mode)}`,
  description: '记录每轮最终得分、消行数、等级和使用方块数。',
  filters: tetrisRecordFilters,
  summaryItems: (summary) => [
    { value: summary.games, label: '挑战次数' },
    { value: formatRecordNumber(summary.bestScore), label: '历史最高分' },
    { value: formatRecordNumber(summary.averageScore), label: '平均得分' },
  ],
  historyOutcome: () => '分',
  historyTitle: (match) => `最终得分 · ${formatRecordNumber(match.scoreValue, '分')}`,
  historyMeta: (match, date) => `${date} · ${match.reason}`,
  detailSection: (match) => {
    const state = match.details.state
    return {
      title: '落块挑战成绩',
      metrics: [
        {
          status: 'success',
          label: '最终得分',
          value: `${Number(state?.score ?? 0).toLocaleString()} 分`,
          note: `到达等级 ${state?.level ?? 1}`,
        },
        {
          status: 'success',
          label: '棋盘表现',
          value: `消除 ${state?.lines ?? 0} 行`,
          note: `使用 ${state?.pieces ?? 0} 个方块 · ${formatMatchDuration(state?.elapsed_ms)}`,
        },
      ],
    }
  },
  detailModeLabel: (match) => tetrisRecordModeLabel(match.gameMode ?? undefined),
  detailWinnerLabel: () => '落块挑战完成',
  detailNote: (match) => match.ranked
    ? '本轮最终得分计入落块挑战排行榜'
    : '本轮得分不计排行榜',
}
