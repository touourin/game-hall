import type {
  BuiltinGameDefinition,
} from './types'
import type { BuiltinArcadeGameKey } from '../types/arcade'

export function defineBuiltinGame<Key extends BuiltinArcadeGameKey>(
  definition: BuiltinGameDefinition<Key>,
): BuiltinGameDefinition<Key> {
  return Object.freeze({
    ...definition,
    catalog: Object.freeze({ ...definition.catalog }),
    capabilities: Object.freeze({ ...definition.capabilities }),
    presentation: Object.freeze({ ...definition.presentation }),
    rules: Object.freeze({
      ...definition.rules,
      defaults: Object.freeze({ ...definition.rules.defaults }),
    }),
  })
}
