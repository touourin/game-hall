import {
  difficultyRecordLabel,
  formatMatchDuration,
  formatRecordDuration,
} from '../../game-platform/recordFormatting'
import type {
  BuiltinGameLeaderboardPresentation,
  BuiltinGameStatsPresentation,
} from '../../game-platform/types'

export const minesweeperLeaderboard: BuiltinGameLeaderboardPresentation = {
  titleSuffix: (mode) => difficultyRecordLabel(mode),
  description: '三种难度独立排名，按个人最快通关时间排序。',
  entryDetail: (entry) =>
    `${entry.games} 次通关 · 平均 ${formatRecordDuration(entry.averageMs)}`,
  entryScore: (entry) => formatRecordDuration(entry.bestMs),
  note: '仅成功清除全部安全方格的服务端计时成绩会进入排行榜。',
}

export const minesweeperStats: BuiltinGameStatsPresentation = {
  titleSuffix: (mode) => difficultyRecordLabel(mode),
  description: '不同难度分别统计通关时间，失败记录也会保留在战绩中。',
  summaryItems: (summary) => [
    { value: summary.games, label: '通关次数' },
    { value: formatMatchDuration(summary.bestMs), label: '最快通关' },
    { value: formatMatchDuration(summary.averageMs), label: '平均用时' },
  ],
  historyOutcome: (match) => match.outcome === 'completed' ? '通' : '雷',
  historyTitle: (match) =>
    `${difficultyRecordLabel(match.gameMode ?? undefined)}扫雷 · ${
      match.scoreMs === null ? '踩中地雷' : formatMatchDuration(match.scoreMs)
    }`,
  historyMeta: (match, date) => `${date} · ${match.reason}`,
  detailWinnerLabel: (match) => match.winner === 'completed'
    ? '扫雷挑战完成'
    : '踩中地雷',
  detailNote: (match) => match.winner === 'completed' && match.ranked
    ? `本次成绩计入${difficultyRecordLabel(match.details.state?.difficulty)}扫雷排行榜`
    : '未通关，不计入排行榜',
}
