import type { GameCatalogEntry } from './gameCatalog'

export type GameCategoryId =
  | 'board'
  | 'social'
  | 'cards'
  | 'solo'
  | 'party'
  | 'community'

export interface GameCategory {
  id: GameCategoryId
  kind: 'official' | 'community'
  eyebrow: string
  name: string
  description: string
  games: readonly GameCatalogEntry[]
}

interface OfficialGameCategoryDefinition {
  id: Exclude<GameCategoryId, 'community'>
  eyebrow: string
  name: string
  description: string
  gameKeys: readonly GameCatalogEntry['key'][]
}

const CATEGORY_DEFINITIONS: readonly OfficialGameCategoryDefinition[] = [
  {
    id: 'board',
    eyebrow: '布局 · 计算',
    name: '棋类竞技',
    description: '从方寸棋盘到军阵铁路，读势、布局与计算共同决定胜负。',
    gameKeys: ['gomoku', 'xiangqi', 'chess', 'go', 'junqi'],
  },
  {
    id: 'social',
    eyebrow: '身份 · 交锋',
    name: '推理社交',
    description: '隐藏身份、有限信息与桌面发言，让每次判断都成为博弈。',
    gameKeys: ['avalon', 'departed_suspicion', 'one_night_werewolf'],
  },
  {
    id: 'cards',
    eyebrow: '牌局 · 心理',
    name: '扑克牌类',
    description: '读牌、配合与筹码决策，在有限手牌中寻找主动权。',
    gameKeys: ['poker', 'doudizhu'],
  },
  {
    id: 'solo',
    eyebrow: '专注 · 突破',
    name: '单人挑战',
    description: '速度、空间、记忆与路线判断，记录每一次自我突破。',
    gameKeys: [
      'reaction',
      'deep_shaft',
      'schulte',
      'critical_crossing',
      'minesweeper',
      'hanoi',
      'tetris',
    ],
  },
  {
    id: 'party',
    eyebrow: '乱斗 · 聚会',
    name: '多人派对',
    description: '实时碰撞与轻策略同场，让朋友聚会既有笑声也有最后一刻的翻盘。',
    gameKeys: ['pixel_push', 'monopoly'],
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

export function buildGameCategories(
  games: readonly GameCatalogEntry[],
): readonly GameCategory[] {
  const officialGames = games.filter((game) => game.source === 'official')
  const communityGames = games.filter((game) => game.source === 'third_party')
  const gameByKey = indexedGames(officialGames)
  const assignedKeys = new Set<string>()

  const officialCategories: GameCategory[] = CATEGORY_DEFINITIONS.map((definition) => {
    const categoryGames = definition.gameKeys.map((key) => {
      const game = gameByKey.get(key)
      if (!game) throw new Error(`游戏分类引用了未注册游戏：${key}`)
      if (assignedKeys.has(key)) throw new Error(`游戏被重复分类：${key}`)
      assignedKeys.add(key)
      return game
    })

    return {
      id: definition.id,
      kind: 'official',
      eyebrow: definition.eyebrow,
      name: definition.name,
      description: definition.description,
      games: categoryGames,
    }
  })

  const unassignedGames = officialGames.filter((game) => !assignedKeys.has(game.key))
  if (unassignedGames.length) {
    throw new Error(
      `官方游戏尚未分类：${unassignedGames.map((game) => game.key).join(', ')}`,
    )
  }

  return [
    ...officialCategories,
    {
      id: 'community',
      kind: 'community',
      eyebrow: '创意 · 扩展',
      name: '社区游戏',
      description: '由社区创作者接入大厅的独立玩法，共用账号、房间与实时对局能力。',
      games: communityGames,
    },
  ]
}
