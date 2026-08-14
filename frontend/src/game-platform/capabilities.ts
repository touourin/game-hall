import type { BuiltinGameCapabilities } from './types'

const boardGameDefaults: BuiltinGameCapabilities = {
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

export function boardGameCapabilities(
  overrides: Partial<BuiltinGameCapabilities> = {},
): BuiltinGameCapabilities {
  return { ...boardGameDefaults, ...overrides }
}

export function soloGameCapabilities(
  overrides: Partial<BuiltinGameCapabilities> = {},
): BuiltinGameCapabilities {
  return { ...soloGameDefaults, ...overrides }
}
