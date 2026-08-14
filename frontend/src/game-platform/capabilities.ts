import type { BuiltinGameCapabilities } from './types'

const boardDuelDefaults: BuiltinGameCapabilities = {
  undo: true,
  draw: true,
  guests: true,
  spectators: true,
  firstPlayer: true,
  replay: false,
  ai: false,
}

const soloGameDefaults: BuiltinGameCapabilities = {
  undo: false,
  draw: false,
  guests: false,
  spectators: false,
  firstPlayer: false,
  replay: false,
  ai: false,
}

export function boardDuelCapabilities(
  overrides: Partial<BuiltinGameCapabilities> = {},
): BuiltinGameCapabilities {
  return { ...boardDuelDefaults, ...overrides }
}

export function soloGameCapabilities(
  overrides: Partial<BuiltinGameCapabilities> = {},
): BuiltinGameCapabilities {
  return { ...soloGameDefaults, ...overrides }
}
