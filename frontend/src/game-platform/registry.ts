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
import type { BuiltinArcadeGameKey } from '../types/arcade'
import type { BuiltinGameDefinition } from './types'

export const BUILTIN_GAME_DEFINITIONS = [
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
] as const satisfies readonly BuiltinGameDefinition[]

const builtinGameDefinitionsByKey = new Map<BuiltinArcadeGameKey, BuiltinGameDefinition>()

for (const definition of BUILTIN_GAME_DEFINITIONS) {
  if (builtinGameDefinitionsByKey.has(definition.key)) {
    throw new Error(`官方游戏模块重复注册：${definition.key}`)
  }
  builtinGameDefinitionsByKey.set(definition.key, definition)
}

export function builtinGameDefinition(
  key: unknown,
): BuiltinGameDefinition | null {
  if (typeof key !== 'string') return null
  return builtinGameDefinitionsByKey.get(key as BuiltinArcadeGameKey) ?? null
}
