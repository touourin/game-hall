import { formatRecordDuration } from '../../game-platform/recordFormatting'
import type { BuiltinGameLeaderboardPresentation } from '../../game-platform/types'

export const schulteLeaderboard: BuiltinGameLeaderboardPresentation = {
  description: '按个人最快完成时间排序，数值越低越快。',
  entryDetail: (entry) =>
    `${entry.games} 次挑战 · 平均 ${formatRecordDuration(entry.averageMs)}`,
  entryScore: (entry) => formatRecordDuration(entry.bestMs),
  note: '排行榜采用服务端计时，并验证 1–25 的完整点击顺序。',
}
