import type { ArcadeGameKey } from './types/arcade'

const NEGOTIATION_GAMES = new Set<ArcadeGameKey>([
  'gomoku',
  'xiangqi',
  'go',
])

export function defaultGameRules(
  gameKey: ArcadeGameKey,
): Record<string, unknown> {
  if (gameKey === 'reaction') return {}
  const options: Record<string, unknown> = { firstPlayer: 'random' }
  if (NEGOTIATION_GAMES.has(gameKey)) {
    options.allowUndo = true
    options.allowDraw = true
  }
  if (gameKey === 'gomoku') {
    options.winRule = 'freestyle'
    options.openingRule = 'swap2'
    options.timeLimitSeconds = 0
  }
  if (gameKey === 'doudizhu') options.variant = 'classic'
  if (gameKey === 'go') {
    options.boardSize = 19
    options.komi = 7.5
  }
  if (gameKey === 'junqi') options.mode = 'dark'
  return options
}

export function withDefaultGameRules(
  gameKey: ArcadeGameKey,
  options: Record<string, unknown>,
): Record<string, unknown> {
  return { ...defaultGameRules(gameKey), ...options }
}

export function gameRuleLabels(
  gameKey: ArcadeGameKey,
  rawOptions: Record<string, unknown>,
): string[] {
  const options = withDefaultGameRules(gameKey, rawOptions)
  if (gameKey === 'reaction') return ['三轮测试']
  const swap2 = gameKey === 'gomoku' && options.openingRule === 'swap2'
  const labels = [
    options.firstPlayer === 'host'
      ? swap2 ? '房主摆子' : gameKey === 'doudizhu' ? '房主首叫' : '房主先手'
      : swap2 ? '随机摆子者' : gameKey === 'doudizhu' ? '随机首叫' : '随机先手',
  ]
  if (NEGOTIATION_GAMES.has(gameKey)) {
    labels.push(options.allowUndo ? '允许悔棋' : '禁止悔棋')
    labels.push(options.allowDraw ? '允许和棋' : '禁止和棋')
  }
  if (gameKey === 'gomoku') {
    labels.unshift('15 路棋盘')
    labels.push(options.openingRule === 'swap2' ? 'Swap2 开局' : '标准开局')
    labels.push(
      options.winRule === 'renju'
        ? '有禁手连珠'
        : options.winRule === 'exact_five'
          ? '正好五子'
          : '自由五子',
    )
    labels.push(
      options.timeLimitSeconds
        ? `每方 ${Number(options.timeLimitSeconds) / 60} 分钟`
        : '不计时',
    )
  }
  if (gameKey === 'go') {
    labels.unshift(`${options.boardSize} 路棋盘`)
    labels.push(`贴目 ${options.komi}`)
  }
  if (gameKey === 'junqi') {
    labels.unshift(options.mode === 'flip' ? '翻棋军旗' : '暗军旗')
  }
  if (gameKey === 'doudizhu') {
    labels.unshift(
      options.variant === 'laizi'
        ? '癞子玩法'
        : options.variant === 'no_shuffle'
          ? '不洗牌玩法'
          : '经典玩法',
    )
    labels.push('叫地主／抢地主')
  }
  return labels
}

export function gameRuleSummary(
  gameKey: ArcadeGameKey,
  options: Record<string, unknown>,
): string {
  return gameRuleLabels(gameKey, options).join(' · ')
}
