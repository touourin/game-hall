import type { LeaderboardEntry } from '../stats'
import { createCompetitiveStatsPresentation } from './recordFormatting'
import { builtinGameDefinition } from './registry'
import type {
  BuiltinGameLeaderboardPresentation,
  BuiltinGameStatsPresentation,
} from './types'

const standardLeaderboardPresentation: BuiltinGameLeaderboardPresentation = {
  description: '按胜场排序，同胜场时依次比较胜率和有效场次。',
  entryDetail: (entry: LeaderboardEntry) =>
    `${entry.wins} 胜${entry.draws ? ` · ${entry.draws} 和` : ''} / ${entry.games} 场`,
  entryScore: (entry: LeaderboardEntry) => `${entry.winRate}%`,
  note: '含 AI 的测试局不会计入排行榜。',
}

export function leaderboardPresentation(
  gameKey: unknown,
): BuiltinGameLeaderboardPresentation {
  return builtinGameDefinition(gameKey)?.records?.leaderboard
    ?? standardLeaderboardPresentation
}

const standardStatsPresentation = createCompetitiveStatsPresentation()

export function statsPresentation(gameKey: unknown): BuiltinGameStatsPresentation {
  return builtinGameDefinition(gameKey)?.records?.stats
    ?? standardStatsPresentation
}
