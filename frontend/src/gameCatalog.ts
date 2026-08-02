import type { ArcadeGameKey, GameCatalogItem } from './types/arcade'

export interface GameCatalogEntry extends GameCatalogItem {
  tone: string
  category: string
}

export const GAME_CATALOG: readonly GameCatalogEntry[] = [
  { key: 'avalon', name: '阿瓦隆', players: '5–10 人', description: '谎言上桌，忠诚接受考验', tone: 'gold', category: '社交推理' },
  { key: 'gomoku', name: '五子棋', players: '2 人', description: '一子定势，五子连珠', tone: 'ink', category: '棋类竞技' },
  { key: 'xiangqi', name: '中国象棋', players: '2 人', description: '隔河列阵，步步攻守', tone: 'red', category: '棋类竞技' },
  { key: 'go', name: '围棋', players: '2 人', description: '方寸之间，围地争先', tone: 'jade', category: '棋类竞技' },
  { key: 'poker', name: '德州扑克', players: '2–8 人', description: '读懂对手，把筹码推向终局', tone: 'poker', category: '扑克对战' },
  { key: 'doudizhu', name: '斗地主', players: '3 人', description: '抢下地主，三人斗到底', tone: 'blue', category: '扑克对战' },
  { key: 'junqi', name: '军旗', players: '2 人', description: '秘密布阵，沿铁路突袭敌旗', tone: 'army', category: '棋类竞技' },
  { key: 'reaction', name: '反应挑战', players: '1 人', description: '盯住信号，挑战毫秒反应', tone: 'pulse', category: '个人挑战' },
  { key: 'schulte', name: '舒尔特方格', players: '1 人', description: '从 1 找到 25，练速度与专注', tone: 'focus', category: '个人挑战' },
  { key: 'minesweeper', name: '扫雷', players: '1 人', description: '排除危险，清空整片雷区', tone: 'mine', category: '个人挑战' },
  { key: 'hanoi', name: '汉诺塔', players: '1 人', description: '移动圆盘，用最少步数通关', tone: 'tower', category: '个人挑战' },
]

export function gameCatalogItem(key: unknown): GameCatalogEntry | null {
  if (typeof key !== 'string') return null
  return GAME_CATALOG.find((game) => game.key === key) ?? null
}

export function isArcadeGameKey(key: unknown): key is ArcadeGameKey {
  return gameCatalogItem(key) !== null
}
