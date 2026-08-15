import avalonGame from '../games/avalon'
import chessGame from '../games/chess'
import criticalCrossingGame from '../games/critical_crossing'
import deepShaftGame from '../games/deep_shaft'
import departedSuspicionGame from '../games/departed_suspicion'
import doudizhuGame from '../games/doudizhu'
import goGame from '../games/go'
import gomokuGame from '../games/gomoku'
import hanoiGame from '../games/hanoi'
import junqiGame from '../games/junqi'
import minesweeperGame from '../games/minesweeper'
import monopolyGame from '../games/monopoly'
import oneNightWerewolfGame from '../games/one_night_werewolf'
import pokerGame from '../games/poker'
import pixelPushGame from '../games/pixel_push'
import reactionGame from '../games/reaction'
import schulteGame from '../games/schulte'
import tetrisGame from '../games/tetris'
import xiangqiGame from '../games/xiangqi'
import { THIRD_PARTY_GAME_REGISTRATIONS } from '../thirdPartyGameRegistry'
import type { ArcadeGameKey, BuiltinArcadeGameKey } from '../types/arcade'
import type { GameRegistration } from './types'

export const BUILTIN_GAME_REGISTRATIONS = [
  avalonGame,
  departedSuspicionGame,
  oneNightWerewolfGame,
  gomokuGame,
  xiangqiGame,
  chessGame,
  goGame,
  pokerGame,
  doudizhuGame,
  junqiGame,
  pixelPushGame,
  reactionGame,
  deepShaftGame,
  schulteGame,
  criticalCrossingGame,
  minesweeperGame,
  hanoiGame,
  tetrisGame,
  monopolyGame,
] as const satisfies readonly GameRegistration<BuiltinArcadeGameKey>[]

export const GAME_REGISTRATIONS: readonly GameRegistration[] = Object.freeze([
  ...BUILTIN_GAME_REGISTRATIONS,
  ...THIRD_PARTY_GAME_REGISTRATIONS,
])

const registrationsByKey = new Map<ArcadeGameKey, GameRegistration>()

for (const registration of GAME_REGISTRATIONS) {
  if (registrationsByKey.has(registration.key)) {
    throw new Error(`游戏模块重复注册：${registration.key}`)
  }
  registrationsByKey.set(registration.key, registration)
}

export function gameRegistration(key: unknown): GameRegistration | null {
  if (typeof key !== 'string') return null
  return registrationsByKey.get(key as ArcadeGameKey) ?? null
}
