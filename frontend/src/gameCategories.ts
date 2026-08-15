import type { GameCatalogEntry } from './gameCatalog'

export type OfficialGameCategoryId =
  | 'board'
  | 'social'
  | 'cards'
  | 'solo'
  | 'party'

export interface OfficialGameCategory {
  id: OfficialGameCategoryId
  eyebrow: string
  name: string
  description: string
  layout: 'wide' | 'standard'
  games: readonly GameCatalogEntry[]
  artworkGames: readonly GameCatalogEntry[]
}

interface OfficialGameCategoryDefinition {
  id: OfficialGameCategoryId
  eyebrow: string
  name: string
  description: string
  layout: OfficialGameCategory['layout']
  gameKeys: readonly GameCatalogEntry['key'][]
  artworkKeys: readonly GameCatalogEntry['key'][]
}

const CATEGORY_DEFINITIONS: readonly OfficialGameCategoryDefinition[] = [
  {
    id: 'board',
    eyebrow: '布局 · 计算',
    name: '棋类竞技',
    description: '从方寸棋盘到军阵铁路，读势、布局与计算共同决定胜负。',
    layout: 'wide',
    gameKeys: ['gomoku', 'xiangqi', 'chess', 'go', 'junqi'],
    artworkKeys: ['go', 'chess', 'xiangqi'],
  },
  {
    id: 'social',
    eyebrow: '身份 · 交锋',
    name: '推理社交',
    description: '隐藏身份、有限信息与桌面发言，让每次判断都成为博弈。',
    layout: 'wide',
    gameKeys: ['avalon', 'departed_suspicion', 'one_night_werewolf'],
    artworkKeys: ['avalon', 'departed_suspicion', 'one_night_werewolf'],
  },
  {
    id: 'cards',
    eyebrow: '牌局 · 心理',
    name: '扑克牌类',
    description: '读牌、配合与筹码决策，在有限手牌中寻找主动权。',
    layout: 'standard',
    gameKeys: ['poker', 'doudizhu'],
    artworkKeys: ['poker', 'doudizhu'],
  },
  {
    id: 'solo',
    eyebrow: '专注 · 突破',
    name: '单人挑战',
    description: '速度、空间、记忆与路线判断，记录每一次自我突破。',
    layout: 'standard',
    gameKeys: [
      'reaction',
      'deep_shaft',
      'schulte',
      'critical_crossing',
      'minesweeper',
      'hanoi',
      'tetris',
    ],
    artworkKeys: ['critical_crossing', 'deep_shaft', 'minesweeper'],
  },
  {
    id: 'party',
    eyebrow: '经营 · 聚会',
    name: '派对经营',
    description: '轻策略与桌面互动并行，适合朋友同桌展开一场城市竞逐。',
    layout: 'standard',
    gameKeys: ['monopoly'],
    artworkKeys: ['monopoly'],
  },
]

function indexedGames(games: readonly GameCatalogEntry[]) {
  const gameByKey = new Map<string, GameCatalogEntry>()
  games.forEach((game) => {
    if (gameByKey.has(game.key)) {
      throw new Error(`游戏分类收到重复游戏：${game.key}`)
    }
    gameByKey.set(game.key, game)
  })
  return gameByKey
}

export function buildOfficialGameCategories(
  games: readonly GameCatalogEntry[],
): readonly OfficialGameCategory[] {
  const gameByKey = indexedGames(games)
  const assignedKeys = new Set<string>()

  const categories = CATEGORY_DEFINITIONS.map((definition) => {
    const categoryGames = definition.gameKeys.map((key) => {
      const game = gameByKey.get(key)
      if (!game) throw new Error(`游戏分类引用了未注册游戏：${key}`)
      if (assignedKeys.has(key)) throw new Error(`游戏被重复分类：${key}`)
      assignedKeys.add(key)
      return game
    })
    const artworkGames = definition.artworkKeys.map((key) => {
      const game = gameByKey.get(key)
      if (!game) throw new Error(`分类视觉引用了未注册游戏：${key}`)
      return game
    })

    return {
      id: definition.id,
      eyebrow: definition.eyebrow,
      name: definition.name,
      description: definition.description,
      layout: definition.layout,
      games: categoryGames,
      artworkGames,
    }
  })

  const unassignedGames = games.filter((game) => !assignedKeys.has(game.key))
  if (unassignedGames.length) {
    throw new Error(
      `官方游戏尚未分类：${unassignedGames.map((game) => game.key).join(', ')}`,
    )
  }

  return categories
}
