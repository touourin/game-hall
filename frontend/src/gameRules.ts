import type { ArcadeGameKey } from './types/arcade'
import { builtinGameDefinition } from './game-platform/registry'
import {
  thirdPartyGameDefaultOptions,
  thirdPartyGameDefinition,
  thirdPartyGameRuleLabels,
} from './thirdPartyGameRegistry'

export function hasGameHandicap(
  gameKey: ArcadeGameKey,
  options: Record<string, unknown>,
): boolean {
  return builtinGameDefinition(gameKey)?.rules.hasHandicap?.(options) ?? false
}

export function applyGameRuleChange(
  gameKey: ArcadeGameKey,
  options: Record<string, unknown>,
  key: string,
  value: unknown,
): Record<string, unknown> {
  const builtinRules = builtinGameDefinition(gameKey)?.rules
  if (builtinRules?.applyChange) {
    return builtinRules.applyChange(options, key, value)
  }
  const next = { ...options, [key]: value }
  if (gameKey === 'avalon' && key === 'mode' && value === 'court_undercurrent') {
    next.ladyEnabled = false
    next.earlyAssassinationEnabled = false
  }
  if (gameKey === 'avalon' && key === 'mode' && value === 'standard') {
    next.shadowMerlinEnabled = false
  }
  return next
}

export function defaultGameRules(
  gameKey: ArcadeGameKey,
): Record<string, unknown> {
  const builtinGame = builtinGameDefinition(gameKey)
  if (builtinGame) return { ...builtinGame.rules.defaults }
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
  if (gameKey === 'one_night_werewolf') {
    return {
      rolePreset: 'standard',
      listed: true,
      allowGuests: true,
      allowSpectators: false,
    }
  }
  if (['reaction', 'deep_shaft', 'schulte', 'survive_three_seconds'].includes(gameKey)) return { allowSpectators: false }
  if (gameKey === 'tetris') {
    return {
      challengeMode: 'timed',
      durationSeconds: 180,
      allowSpectators: false,
    }
  }
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
  if (gameKey === 'doudizhu') options.variant = 'classic'
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
  const builtinGame = builtinGameDefinition(gameKey)
  if (builtinGame) return builtinGame.rules.labels(options)
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
  if (gameKey === 'one_night_werewolf') {
    const preset = options.rolePreset === 'beginner'
      ? '初见月夜'
      : options.rolePreset === 'chaos'
        ? '混沌之夜'
        : '标准疑云'
    return [
      '3–10 人',
      preset,
      '不限时讨论',
      options.listed ? '公开房间' : '私密房间',
      options.allowGuests ? '允许游客' : '仅登录玩家',
    ]
  }
  if (gameKey === 'reaction') return ['三轮测试']
  if (gameKey === 'deep_shaft') return ['100 层挑战', '左右移动', '服务端轨迹重放']
  if (gameKey === 'schulte') return ['5×5 标准挑战', '服务端计时']
  if (gameKey === 'survive_three_seconds') return ['3 秒极限挑战', '服务端轨迹重放']
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
  if (gameKey === 'tetris') {
    return [
      options.challengeMode === 'timed'
        ? `${Number(options.durationSeconds) / 60} 分钟限时`
        : '无限挑战',
      '10×20 标准棋盘',
      '7-bag 随机序列',
    ]
  }
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
  const labels = [
    options.firstPlayer === 'host'
      ? gameKey === 'doudizhu' ? '房主首叫' : '房主先手'
      : gameKey === 'doudizhu' ? '随机首叫' : '随机先手',
  ]
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
