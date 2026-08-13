import { createCompetitiveStatsPresentation } from './recordFormatting'
import { builtinGameDefinition } from './registry'
import type { BuiltinGameStatsPresentation } from './types'

export const standardStatsPresentation = createCompetitiveStatsPresentation()

export function statsPresentation(gameKey: unknown): BuiltinGameStatsPresentation {
  return builtinGameDefinition(gameKey)?.records?.stats
    ?? standardStatsPresentation
}
