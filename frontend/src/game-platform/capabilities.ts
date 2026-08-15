import type { BuiltinGameCapabilities } from './types'

const boardDuelDefaults: BuiltinGameCapabilities = {
  undo: true,
  draw: true,
  guests: true,
  spectators: true,
  spectatorFrames: false,
  firstPlayer: true,
  replay: false,
  ai: false,
}

const soloGameDefaults: BuiltinGameCapabilities = {
  undo: false,
  draw: false,
  guests: false,
  spectators: true,
  spectatorFrames: false,
  firstPlayer: false,
  replay: false,
  ai: false,
}

const socialTableDefaults: BuiltinGameCapabilities = {
  undo: false,
  draw: false,
  guests: true,
  spectators: true,
  spectatorFrames: false,
  firstPlayer: true,
  replay: false,
  ai: false,
}

type SocialTableCapabilityOverrides = Partial<Pick<
  BuiltinGameCapabilities,
  'guests' | 'spectators' | 'firstPlayer' | 'replay' | 'ai'
>>

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

export function socialTableCapabilities(
  overrides: SocialTableCapabilityOverrides = {},
): BuiltinGameCapabilities {
  return { ...socialTableDefaults, ...overrides }
}
