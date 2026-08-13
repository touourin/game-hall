import type { ArcadeGameKey, GameCatalogItem } from './types/arcade'
import { THIRD_PARTY_GAME_PLUGINS } from './thirdPartyGameRegistry'

export interface GameCatalogEntry extends GameCatalogItem {
  tone: string
  category: string
}

const BUILTIN_GAME_CATALOG: readonly GameCatalogEntry[] = [
  { key: 'avalon', name: '阿瓦隆', players: '5–10 人', description: '谎言上桌，忠诚接受考验', tone: 'gold', category: '社交推理' },
  { key: 'departed_suspicion', name: '无间疑云', players: '4–8 人', description: '查底细、抢装备，在枪口转向前找出敌方领袖', tone: 'suspicion', category: '身份推理' },
  { key: 'one_night_werewolf', name: '一夜狼人', players: '3–10 人', description: '一晚换位，天亮后只投一次', tone: 'moon', category: '社交推理' },
  { key: 'gomoku', name: '五子棋', players: '2 人', description: '一子定势，五子连珠', tone: 'ink', category: '棋类竞技' },
  { key: 'xiangqi', name: '中国象棋', players: '2 人', description: '隔河列阵，步步攻守', tone: 'red', category: '棋类竞技' },
  { key: 'go', name: '围棋', players: '2 人', description: '方寸之间，围地争先', tone: 'jade', category: '棋类竞技' },
  { key: 'poker', name: '德州扑克', players: '2–8 人', description: '读懂对手，把筹码推向终局', tone: 'poker', category: '扑克对战' },
  { key: 'doudizhu', name: '斗地主', players: '3 人', description: '抢下地主，三人斗到底', tone: 'blue', category: '扑克对战' },
  { key: 'junqi', name: '军旗', players: '2 人', description: '秘密布阵，沿铁路突袭敌旗', tone: 'army', category: '棋类竞技' },
  { key: 'reaction', name: '反应挑战', players: '1 人', description: '盯住信号，挑战毫秒反应', tone: 'pulse', category: '个人挑战' },
  { key: 'schulte', name: '舒尔特方格', players: '1 人', description: '从 1 找到 25，练速度与专注', tone: 'focus', category: '个人挑战' },
  { key: 'survive_three_seconds', name: '坚持三秒', players: '1 人', description: '弹幕从四面袭来，撑过三秒就是胜利', tone: 'barrage', category: '个人挑战' },
  { key: 'minesweeper', name: '扫雷', players: '1 人', description: '排除危险，清空整片雷区', tone: 'mine', category: '个人挑战' },
  { key: 'hanoi', name: '汉诺塔', players: '1 人', description: '移动圆盘，用最少步数通关', tone: 'tower', category: '个人挑战' },
  { key: 'tetris', name: '落块挑战', players: '1 人', description: '排列方块、连续消行，冲击更高分数', tone: 'blocks', category: '个人挑战' },
  { key: 'monopoly', name: '大富翁', players: '2–4 人', description: '买下整座城，让财富沿街生长', tone: 'fortune', category: '派对桌游' },
]

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
  if (['reaction', 'schulte', 'survive_three_seconds', 'minesweeper', 'hanoi', 'tetris'].includes(key)) return true
  const plugin = THIRD_PARTY_GAME_PLUGINS.find(({ manifest }) => manifest.id === key)
  return plugin?.manifest.players.max === 1
}
