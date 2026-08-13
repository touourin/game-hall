import type { ArcadeGameKey, GameCatalogItem } from './types/arcade'
import { BUILTIN_GAME_DEFINITIONS } from './game-platform/registry'
import { builtinGamePlayerLabel } from './game-platform/types'
import { THIRD_PARTY_GAME_PLUGINS } from './thirdPartyGameRegistry'

export interface GameCatalogEntry extends GameCatalogItem {
  tone: string
  category: string
}

const LEGACY_BUILTIN_GAME_CATALOG: readonly GameCatalogEntry[] = [
  { key: 'avalon', name: '阿瓦隆', players: '5–10 人', description: '谎言上桌，忠诚接受考验', tone: 'gold', category: '社交推理' },
  { key: 'departed_suspicion', name: '无间疑云', players: '4–8 人', description: '查底细、抢装备，在枪口转向前找出敌方领袖', tone: 'suspicion', category: '身份推理' },
  { key: 'one_night_werewolf', name: '一夜狼人', players: '3–10 人', description: '一晚换位，天亮后只投一次', tone: 'moon', category: '社交推理' },
]

const BUILTIN_GAME_ORDER: readonly ArcadeGameKey[] = [
  'avalon',
  'departed_suspicion',
  'one_night_werewolf',
  'gomoku',
  'xiangqi',
  'chess',
  'go',
  'poker',
  'doudizhu',
  'junqi',
  'reaction',
  'deep_shaft',
  'schulte',
  'survive_three_seconds',
  'minesweeper',
  'hanoi',
  'tetris',
  'monopoly',
]

const builtinGameOrder = new Map(
  BUILTIN_GAME_ORDER.map((key, index) => [key, index * 10]),
)

const BUILTIN_GAME_CATALOG: readonly GameCatalogEntry[] = [
  ...LEGACY_BUILTIN_GAME_CATALOG.map((game) => ({
    order: builtinGameOrder.get(game.key) ?? Number.MAX_SAFE_INTEGER,
    game,
  })),
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

const builtinKeys = BUILTIN_GAME_CATALOG.map((game) => game.key)
if (
  builtinKeys.length !== BUILTIN_GAME_ORDER.length
  || new Set(builtinKeys).size !== builtinKeys.length
  || builtinKeys.some((key, index) => key !== BUILTIN_GAME_ORDER[index])
) {
  throw new Error('官方游戏目录与模块注册表不一致')
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

export function isArcadeGameKey(key: unknown): key is ArcadeGameKey {
  return gameCatalogItem(key) !== null
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
