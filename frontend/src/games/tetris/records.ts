import { tetrisRecordModeLabel } from '../../game-platform/recordFormatting'
import type {
  BuiltinGameLeaderboardPresentation,
  BuiltinGameStatsPresentation,
} from '../../game-platform/types'

export const tetrisLeaderboard: BuiltinGameLeaderboardPresentation = {
  titleSuffix: (mode) => ` · ${tetrisRecordModeLabel(mode)}`,
  description: '按个人历史最高得分排序，分数越高排名越前。',
  entryDetail: (entry) =>
    `${entry.games} 次挑战 · 平均 ${entry.averageScore?.toLocaleString()} 分`,
  entryScore: (entry) => `${entry.bestScore?.toLocaleString()} 分`,
  note: '每轮结束后保存最终得分；最高分优先，总平均分用于同分参考。',
}

export const tetrisStats: BuiltinGameStatsPresentation = {
  titleSuffix: (mode) => ` · ${tetrisRecordModeLabel(mode)}`,
  description: '记录每轮最终得分、消行数、等级和使用方块数。',
  summaryItems: (summary) => [
    { value: summary.games, label: '挑战次数' },
    { value: summary.bestScore?.toLocaleString() ?? '—', label: '历史最高分' },
    { value: summary.averageScore?.toLocaleString() ?? '—', label: '平均得分' },
  ],
  historyOutcome: () => '分',
  historyTitle: (match) => `最终得分 · ${match.scoreValue?.toLocaleString()} 分`,
  historyMeta: (match, date) => `${date} · ${match.reason}`,
  detailModeLabel: (match) => tetrisRecordModeLabel(match.gameMode ?? undefined),
  detailWinnerLabel: () => '落块挑战完成',
  detailNote: (match) => match.ranked
    ? '本轮最终得分计入落块挑战排行榜'
    : '本轮得分不计排行榜',
}
