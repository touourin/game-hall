import { tetrisRecordModeLabel } from '../../game-platform/recordFormatting'
import type { BuiltinGameLeaderboardPresentation } from '../../game-platform/types'

export const tetrisLeaderboard: BuiltinGameLeaderboardPresentation = {
  titleSuffix: (mode) => ` · ${tetrisRecordModeLabel(mode)}`,
  description: '按个人历史最高得分排序，分数越高排名越前。',
  entryDetail: (entry) =>
    `${entry.games} 次挑战 · 平均 ${entry.averageScore?.toLocaleString()} 分`,
  entryScore: (entry) => `${entry.bestScore?.toLocaleString()} 分`,
  note: '每轮结束后保存最终得分；最高分优先，总平均分用于同分参考。',
}
