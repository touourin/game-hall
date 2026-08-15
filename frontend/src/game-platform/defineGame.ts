import type {
  BuiltinGameDefinition,
  GameRegistration,
} from './types'
import type { BuiltinArcadeGameKey } from '../types/arcade'

export function defineBuiltinGame<Key extends BuiltinArcadeGameKey>(
  definition: BuiltinGameDefinition<Key>,
): GameRegistration<Key> {
  return Object.freeze({
    ...definition,
    source: 'official' as const,
    availability: 'enabled' as const,
    catalog: Object.freeze({ ...definition.catalog }),
    capabilities: Object.freeze({ ...definition.capabilities }),
    presentation: Object.freeze({
      ...definition.presentation,
      roomShell: definition.presentation.roomShell
        ? Object.freeze({ ...definition.presentation.roomShell })
        : undefined,
      solo: definition.presentation.solo
        ? Object.freeze({ ...definition.presentation.solo })
        : undefined,
    }),
    rules: Object.freeze({
      ...definition.rules,
      defaults: Object.freeze({ ...definition.rules.defaults }),
    }),
    records: definition.records
      ? Object.freeze({
          ...definition.records,
          leaderboard: definition.records.leaderboard
            ? Object.freeze({
                ...definition.records.leaderboard,
                filters: definition.records.leaderboard.filters
                  ? Object.freeze([...definition.records.leaderboard.filters])
                  : undefined,
              })
            : undefined,
          stats: definition.records.stats
            ? Object.freeze({
                ...definition.records.stats,
                filters: definition.records.stats.filters
                  ? Object.freeze([...definition.records.stats.filters])
                  : undefined,
              })
            : undefined,
        })
      : undefined,
  })
}
