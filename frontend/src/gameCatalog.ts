import type { GameCatalogItem } from './types/arcade'
import { BUILTIN_GAME_DEFINITIONS } from './game-platform/registry'
import { builtinGamePlayerLabel } from './game-platform/types'
import { THIRD_PARTY_GAME_PLUGINS } from './thirdPartyGameRegistry'

export interface GameCatalogEntry extends GameCatalogItem {
  tone: string
  category: string
}

const BUILTIN_GAME_CATALOG: readonly GameCatalogEntry[] = [
  ...BUILTIN_GAME_DEFINITIONS.map((definition) => ({
    order: definition.catalog.order,
    game: {
      key: definition.key,
      name: definition.catalog.name,
      players: builtinGamePlayerLabel(definition.catalog.players),
      description: definition.catalog.description,
      tone: definition.catalog.tone,
      category: definition.catalog.category,
    },
  })),
].sort((left, right) => left.order - right.order).map(({ game }) => game)

const builtinOrders = BUILTIN_GAME_DEFINITIONS.map(
  (definition) => definition.catalog.order,
)
if (new Set(builtinOrders).size !== builtinOrders.length) {
  throw new Error('官方游戏目录存在重复排序')
}

export const GAME_CATALOG: readonly GameCatalogEntry[] = [
  ...BUILTIN_GAME_CATALOG,
  ...THIRD_PARTY_GAME_PLUGINS.map(({ manifest }) => ({
    key: manifest.id,
    name: manifest.name,
    players: manifest.players.label
      ?? (manifest.players.min === manifest.players.max
        ? `${manifest.players.min} 人`
        : `${manifest.players.min}–${manifest.players.max} 人`),
    description: manifest.description,
    tone: manifest.tone,
    category: manifest.category,
  })),
]

export function gameCatalogItem(key: unknown): GameCatalogEntry | null {
  if (typeof key !== 'string') return null
  return GAME_CATALOG.find((game) => game.key === key) ?? null
}

export function isSoloGameKey(key: unknown): boolean {
  if (typeof key !== 'string') return false
  const builtinGame = BUILTIN_GAME_DEFINITIONS.find(
    (definition) => definition.key === key,
  )
  if (builtinGame) return builtinGame.catalog.players.max === 1
  const plugin = THIRD_PARTY_GAME_PLUGINS.find(({ manifest }) => manifest.id === key)
  return plugin?.manifest.players.max === 1
}
