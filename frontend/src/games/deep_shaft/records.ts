import type { BuiltinGameLeaderboardPresentation } from '../../game-platform/types'

export const deepShaftLeaderboard: BuiltinGameLeaderboardPresentation = {
  description: '按个人历史最深层数排序，抵达层数越深排名越前。',
  entryDetail: (entry) =>
    `${entry.games} 次挑战 · 平均 ${entry.averageScore?.toLocaleString()} 层`,
  entryScore: (entry) => `${entry.bestScore?.toLocaleString()} 层`,
  note: '服务器会根据随机种子重放全部左右输入，再保存实际抵达的最深层数。',
}
