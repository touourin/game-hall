import type { BuiltinGameLeaderboardPresentation } from '../../game-platform/types'

export const surviveThreeSecondsLeaderboard: BuiltinGameLeaderboardPresentation = {
  description: '按成功坚持三秒的次数排序，同次数时比较存活率。',
  entryDetail: (entry) => `${entry.games} 次挑战 · ${entry.wins} 次生还`,
  entryScore: (entry) => `${entry.wins} 次`,
  note: '每次挑战都由服务器重放 180 帧方向输入后判定结果。',
}
