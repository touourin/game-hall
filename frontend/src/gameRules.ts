import { gameRegistration } from './game-platform/registry'
import type { ArcadeGameKey } from './types/arcade'

export function hasGameHandicap(
  gameKey: ArcadeGameKey,
  options: Record<string, unknown>,
): boolean {
  return gameRegistration(gameKey)?.rules.hasHandicap?.(options) ?? false
}

export function applyGameRuleChange(
  gameKey: ArcadeGameKey,
  options: Record<string, unknown>,
  key: string,
  value: unknown,
): Record<string, unknown> {
  const applyChange = gameRegistration(gameKey)?.rules.applyChange
  return applyChange
    ? applyChange(options, key, value)
    : { ...options, [key]: value }
}

export function defaultGameRules(
  gameKey: ArcadeGameKey,
): Record<string, unknown> {
  const registration = gameRegistration(gameKey)
  if (registration) return { ...registration.rules.defaults }
  return {
    firstPlayer: 'random',
    allowGuests: true,
    allowSpectators: true,
  }
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
  const registration = gameRegistration(gameKey)
  if (registration) return registration.rules.labels(options)
  return [
    options.firstPlayer === 'host' ? '房主先手' : '随机先手',
    options.allowGuests ? '允许游客' : '仅登录玩家',
  ]
}
