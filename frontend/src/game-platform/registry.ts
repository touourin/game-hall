import type { Component } from 'vue'
import chessGame from '../games/chess'
import deepShaftGame from '../games/deep_shaft'
import doudizhuGame from '../games/doudizhu'
import goGame from '../games/go'
import gomokuGame from '../games/gomoku'
import hanoiGame from '../games/hanoi'
import junqiGame from '../games/junqi'
import minesweeperGame from '../games/minesweeper'
import monopolyGame from '../games/monopoly'
import pokerGame from '../games/poker'
import reactionGame from '../games/reaction'
import schulteGame from '../games/schulte'
import surviveThreeSecondsGame from '../games/survive_three_seconds'
import tetrisGame from '../games/tetris'
import xiangqiGame from '../games/xiangqi'
import type { BuiltinArcadeGameKey } from '../types/arcade'
import type { BuiltinGameDefinition } from './types'

export const BUILTIN_GAME_DEFINITIONS = [
  gomokuGame,
  xiangqiGame,
  chessGame,
  goGame,
  pokerGame,
  doudizhuGame,
  junqiGame,
  reactionGame,
  deepShaftGame,
  schulteGame,
  surviveThreeSecondsGame,
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

export function builtinGameComponent(key: unknown): Component | null {
  return builtinGameDefinition(key)?.presentation.component ?? null
}
