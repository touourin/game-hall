import {
  difficultyRecordLabel,
  formatRecordDuration,
} from '../../game-platform/recordFormatting'
import type { BuiltinGameLeaderboardPresentation } from '../../game-platform/types'

export const minesweeperLeaderboard: BuiltinGameLeaderboardPresentation = {
  titleSuffix: (mode) => difficultyRecordLabel(mode),
  description: '三种难度独立排名，按个人最快通关时间排序。',
  entryDetail: (entry) =>
    `${entry.games} 次通关 · 平均 ${formatRecordDuration(entry.averageMs)}`,
  entryScore: (entry) => formatRecordDuration(entry.bestMs),
  note: '仅成功清除全部安全方格的服务端计时成绩会进入排行榜。',
}
