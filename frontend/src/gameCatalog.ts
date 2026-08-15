import { GAME_REGISTRATIONS, gameRegistration } from './game-platform/registry'
import { gamePlayerLabel, type GameSource } from './game-platform/types'
import type { GameCatalogItem } from './types/arcade'

export interface GameCatalogEntry extends GameCatalogItem {
  source: GameSource
  tone: string
  category: string
}

function catalogEntry(
  registration: NonNullable<ReturnType<typeof gameRegistration>>,
): GameCatalogEntry {
  return {
    key: registration.key,
    source: registration.source,
    name: registration.catalog.name,
    players: gamePlayerLabel(registration.catalog.players),
    description: registration.catalog.description,
    tone: registration.catalog.tone,
    category: registration.catalog.category,
  }
}

export const GAME_CATALOG: readonly GameCatalogEntry[] = Object.freeze(
  GAME_REGISTRATIONS
    .filter((registration) => registration.availability === 'enabled')
    .sort((left, right) => (
      Number(left.source !== 'official') - Number(right.source !== 'official')
      || left.catalog.order - right.catalog.order
    ))
    .map(catalogEntry),
)

export function gameCatalogItem(key: unknown): GameCatalogEntry | null {
  if (typeof key !== 'string') return null
  const published = GAME_CATALOG.find((game) => game.key === key)
  if (published) return published
  const registration = gameRegistration(key)
  return registration ? catalogEntry(registration) : null
}

export function isSoloGameKey(key: unknown): boolean {
  return gameRegistration(key)?.catalog.players.max === 1
}
