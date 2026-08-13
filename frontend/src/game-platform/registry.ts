import type { Component } from 'vue'
import chessGame from '../games/chess'
import type { BuiltinArcadeGameKey } from '../types/arcade'
import type { BuiltinGameDefinition } from './types'

export const BUILTIN_GAME_DEFINITIONS = [
  chessGame,
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
