import type { ArcadeGameKey } from './types/arcade'
import {
  thirdPartyGameDefaultOptions,
  thirdPartyGameDefinition,
  thirdPartyGameRuleLabels,
} from './thirdPartyGameRegistry'

const NEGOTIATION_GAMES = new Set<ArcadeGameKey>([
  'gomoku',
  'xiangqi',
  'go',
])

export const XIANGQI_HANDICAP_OPTIONS = [
  { value: 'none', label: '不让子' },
  { value: 'cannon', label: '让炮' },
  { value: 'horse', label: '让马' },
  { value: 'rook', label: '让车' },
  { value: 'nine', label: '让九子' },
] as const

export const GO_HANDICAP_OPTIONS = [0, 2, 3, 6, 9] as const

export function hasGameHandicap(
  gameKey: ArcadeGameKey,
  options: Record<string, unknown>,
): boolean {
  if (gameKey === 'xiangqi') {
    return typeof options.handicap === 'string' && options.handicap !== 'none'
  }
  return gameKey === 'go' && Number(options.handicap) > 0
}

export function applyGameRuleChange(
  gameKey: ArcadeGameKey,
  options: Record<string, unknown>,
  key: string,
  value: unknown,
): Record<string, unknown> {
  const next = { ...options, [key]: value }
  if (gameKey === 'gomoku' && key === 'winRule' && value === 'renju') {
    next.openingRule = 'standard'
  }
  if (gameKey === 'avalon' && key === 'mode' && value === 'court_undercurrent') {
    next.ladyEnabled = false
    next.earlyAssassinationEnabled = false
  }
  if (gameKey === 'avalon' && key === 'mode' && value === 'standard') {
    next.shadowMerlinEnabled = false
  }
  if (gameKey === 'go' && key === 'boardSize' && value !== 19) {
    next.handicap = 0
  }
  if (gameKey === 'go' && key === 'handicap' && value !== 0) {
    next.boardSize = 19
    next.komi = 0
  }
  return next
}

export function defaultGameRules(
  gameKey: ArcadeGameKey,
): Record<string, unknown> {
  if (thirdPartyGameDefinition(gameKey)) {
    return {
      firstPlayer: 'random',
      allowGuests: true,
      allowSpectators: true,
      ...thirdPartyGameDefaultOptions(gameKey),
    }
  }
  if (gameKey === 'avalon') {
    return {
      mode: 'standard',
      shadowMerlinEnabled: false,
      ladyEnabled: true,
      listed: true,
      allowGuests: true,
      allowSpectators: true,
      earlyAssassinationEnabled: false,
    }
  }
  if (gameKey === 'departed_suspicion') {
    return {
      equipmentSet: 'bombers',
      firstPlayer: 'random',
      allowGuests: true,
      allowSpectators: true,
    }
  }
  if (gameKey === 'reaction' || gameKey === 'schulte' || gameKey === 'tetris') return { allowSpectators: false }
  if (gameKey === 'minesweeper') return { difficulty: 'beginner', allowSpectators: true }
  if (gameKey === 'hanoi') return { discCount: 5, allowSpectators: true }
  const options: Record<string, unknown> = {
    firstPlayer: 'random',
    allowGuests: true,
    allowSpectators: true,
  }
  if (gameKey === 'poker') {
    options.startingChips = 1000
    options.smallBlind = 10
  }
  if (gameKey === 'monopoly') {
    options.startingCash = 8000
    options.maxRounds = 20
  }
  if (NEGOTIATION_GAMES.has(gameKey)) {
    options.allowUndo = true
    options.allowDraw = true
  }
  if (gameKey === 'gomoku') {
    options.winRule = 'exact_five'
    options.openingRule = 'swap2'
  }
  if (gameKey === 'xiangqi') {
    options.captureHintsEnabled = true
    options.handicap = 'none'
    options.handicapGiver = 'host'
  }
  if (gameKey === 'doudizhu') options.variant = 'classic'
  if (gameKey === 'go') {
    options.boardSize = 19
    options.komi = 7.5
    options.handicap = 0
    options.handicapGiver = 'host'
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
  if (thirdPartyGameDefinition(gameKey)) {
    const labels = thirdPartyGameRuleLabels(gameKey)
    labels.push(options.allowGuests ? '允许游客' : '仅登录玩家')
    return labels
  }
  if (gameKey === 'avalon') {
    const labels = [
      options.mode === 'court_undercurrent' ? '王庭暗流' : '标准阿瓦隆',
      options.listed ? '公开房间' : '私密房间',
      options.allowGuests ? '允许游客' : '仅登录玩家',
    ]
    if (options.mode !== 'court_undercurrent') {
      labels.push(options.ladyEnabled ? '启用湖中仙女' : '不启用湖中仙女')
      if (options.earlyAssassinationEnabled) labels.push('允许提前刺杀')
    }
    if (
      options.mode === 'court_undercurrent' &&
      options.shadowMerlinEnabled
    ) labels.push('暗影梅林扩展')
    return labels
  }
  if (gameKey === 'departed_suspicion') {
    return [
      '4–8 人基础身份局',
      options.equipmentSet === 'base' ? '基础16张装备' : '基础＋炸弹客/叛徒21张装备',
      options.firstPlayer === 'host' ? '房主先手' : '随机先手',
      options.allowGuests ? '允许游客' : '仅登录玩家',
    ]
  }
  if (gameKey === 'reaction') return ['三轮测试']
  if (gameKey === 'schulte') return ['5×5 标准挑战', '服务端计时']
  if (gameKey === 'minesweeper') {
    const difficulty = String(options.difficulty)
    if (difficulty === 'expert') return ['高级', '16×30', '99 雷']
    if (difficulty === 'intermediate') return ['中级', '16×16', '40 雷']
    return ['初级', '9×9', '10 雷']
  }
  if (gameKey === 'hanoi') {
    const discCount = Number(options.discCount)
    return [`${discCount} 层圆盘`, `理论最少 ${2 ** discCount - 1} 步`]
  }
  if (gameKey === 'tetris') return ['10×20 标准棋盘', '7-bag 随机序列']
  if (gameKey === 'poker') {
    const smallBlind = Number(options.smallBlind)
    return [
      '2–8 人',
      `起始 ${Number(options.startingChips)} 筹码`,
      `盲注 ${smallBlind}/${smallBlind * 2}`,
      options.allowGuests ? '允许游客' : '仅登录玩家',
    ]
  }
  if (gameKey === 'monopoly') {
    return [
      '2–4 人',
      `起始资金 ${Number(options.startingCash)}`,
      `${Number(options.maxRounds)} 回合资产赛`,
      '同色地块可升级',
      options.allowGuests ? '允许游客' : '仅登录玩家',
    ]
  }
  const swap2 = gameKey === 'gomoku' && options.openingRule === 'swap2'
  const handicap = hasGameHandicap(gameKey, options)
  const labels = [
    handicap
      ? options.handicapGiver === 'host' ? '房主让子' : '对手让子'
      : options.firstPlayer === 'host'
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
  }
  if (gameKey === 'go') {
    labels.unshift(`${options.boardSize} 路棋盘`)
    if (Number(options.handicap) > 0) labels.push(`让 ${options.handicap} 子`)
    labels.push(`贴目 ${options.komi}`)
  }
  if (gameKey === 'xiangqi') {
    const selectedHandicap = XIANGQI_HANDICAP_OPTIONS.find(
      ({ value }) => value !== 'none' && value === options.handicap,
    )
    if (selectedHandicap) {
      labels.push(selectedHandicap.label)
    }
    labels.push(
      options.captureHintsEnabled ? '吃子提醒' : '关闭吃子提醒',
    )
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
  labels.push(options.allowGuests ? '允许游客' : '仅登录玩家')
  return labels
}

export function gameRuleSummary(
  gameKey: ArcadeGameKey,
  options: Record<string, unknown>,
): string {
  return gameRuleLabels(gameKey, options).join(' · ')
}
