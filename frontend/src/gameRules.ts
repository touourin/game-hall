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
  const labels = [
    options.firstPlayer === 'host' ? '房主先手' : '随机先手',
  ]
  labels.push(options.allowGuests ? '允许游客' : '仅登录玩家')
  return labels
}
