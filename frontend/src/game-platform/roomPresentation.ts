import { builtinGameDefinition } from './registry'
import type { BuiltinGameRoomShellPresentation } from './types'

export const standardRoomShellPresentation: BuiltinGameRoomShellPresentation = {}

export function roomShellPresentation(
  gameKey: unknown,
): BuiltinGameRoomShellPresentation {
  return builtinGameDefinition(gameKey)?.presentation.roomShell
    ?? standardRoomShellPresentation
}
