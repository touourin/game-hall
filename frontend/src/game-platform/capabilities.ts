import type { BuiltinGameCapabilities } from './types'

const soloGameDefaults: BuiltinGameCapabilities = {
  undo: false,
  draw: false,
  guests: false,
  spectators: false,
  firstPlayer: false,
  replay: false,
  ai: false,
}

export function soloGameCapabilities(
  overrides: Partial<BuiltinGameCapabilities> = {},
): BuiltinGameCapabilities {
  return { ...soloGameDefaults, ...overrides }
}
