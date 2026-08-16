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
  defaultMode: 'beginner',
  titleSuffix: (mode) => ` · ${difficultyRecordLabel(mode)}`,
  description: '三种难度独立排名，按个人最快通关时间排序。',
  filters: [
    { label: '初级', mode: 'beginner' },
    { label: '中级', mode: 'intermediate' },
    { label: '高级', mode: 'expert' },
  ],
  entryDetail: (entry) =>
    `${entry.games} 次通关 · 平均 ${formatRecordDuration(entry.averageMs)}`,
  entryScore: (entry) => formatRecordDuration(entry.bestMs),
  note: '仅成功清除全部安全方格的服务端计时成绩会进入排行榜。',
}

export const minesweeperStats: BuiltinGameStatsPresentation = {
  defaultMode: minesweeperLeaderboard.defaultMode,
  titleSuffix: (mode) => ` · ${difficultyRecordLabel(mode)}`,
  description: '不同难度分别统计通关时间，失败记录也会保留在战绩中。',
  filters: minesweeperLeaderboard.filters,
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
  detailSection: (match) => {
    const state = match.details.state
    return {
      title: '扫雷挑战成绩',
      metrics: [
        {
          status: match.winner === 'completed' ? 'success' : 'failed',
          label: `${difficultyRecordLabel(state?.difficulty)} · ${state?.rows ?? 0}×${state?.columns ?? 0}`,
          value: match.winner === 'completed'
            ? formatMatchDuration(state?.elapsed_ms)
            : '踩中地雷',
          note: `${state?.mine_count ?? 0} 雷 · 已翻开 ${state?.revealed_count ?? 0} 个安全格`,
        },
        {
          status: 'success',
          label: '本轮标记',
          value: `${state?.flagged_count ?? 0} 面旗帜`,
          note: '首次翻开区域由服务端保证安全',
        },
      ],
    }
  },
  detailWinnerLabel: (match) => match.winner === 'completed'
    ? '扫雷挑战完成'
    : '踩中地雷',
  detailNote: (match) => match.winner === 'completed' && match.ranked
    ? `本次成绩计入${difficultyRecordLabel(match.details.state?.difficulty)}扫雷排行榜`
    : '未通关，不计入排行榜',
}
