import type { BuiltinGameLeaderboardPresentation } from '../../game-platform/types'

export const hanoiLeaderboard: BuiltinGameLeaderboardPresentation = {
  description: '按累计通关次数排序，同次数时优先更早完成挑战的玩家。',
  entryDetail: (entry) => `${entry.games} 次挑战 · ${entry.wins} 次通关`,
  entryScore: (entry) => `${entry.wins} 次`,
  note: '不同层数都会累计为一次有效通关，详细步数和时间保存在个人战绩中。',
}
