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
  const options: Record<string, unknown> = {
    firstPlayer: 'random',
    allowGuests: true,
    allowSpectators: true,
  }
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
  const labels = [
    options.firstPlayer === 'host' ? '房主先手' : '随机先手',
  ]
  labels.push(options.allowGuests ? '允许游客' : '仅登录玩家')
  return labels
}

export function gameRuleSummary(
  gameKey: ArcadeGameKey,
  options: Record<string, unknown>,
): string {
  return gameRuleLabels(gameKey, options).join(' · ')
}
