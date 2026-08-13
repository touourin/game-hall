import type { Component } from 'vue'
import type { BuiltinArcadeGameKey } from '../types/arcade'

export type BuiltinGameRoomLayout = 'standard' | 'wide' | 'immersive'
export type BuiltinGameSkinKind = 'board' | 'cards'

export interface BuiltinGameCatalogMetadata {
  order: number
  name: string
  players: {
    min: number
    max: number
    label?: string
  }
  description: string
  tone: string
  category: string
  artwork: string
}

export function builtinGamePlayerLabel(
  players: BuiltinGameCatalogMetadata['players'],
): string {
  if (players.label) return players.label
  return players.min === players.max
    ? `${players.min} 人`
    : `${players.min}–${players.max} 人`
}

export interface BuiltinGameCapabilities {
  undo: boolean
  draw: boolean
  guests: boolean
  spectators: boolean
  firstPlayer: boolean
  replay: boolean
  ai: boolean
}

export interface BuiltinGamePresentation {
  component: Component
  roomLayout: BuiltinGameRoomLayout
  skinKind: BuiltinGameSkinKind | null
}

export interface BuiltinGameRuleSettingsProps {
  modelValue: Readonly<Record<string, unknown>>
}

export interface BuiltinGameRuleSettingsEmits {
  change: [key: string, value: unknown]
}

export interface BuiltinGameFirstPlayerCopy {
  title: string
  description: string
  randomDescription: string
  hostDescription: string
}

export interface BuiltinGameRules {
  defaults: Readonly<Record<string, unknown>>
  labels: (options: Readonly<Record<string, unknown>>) => string[]
  settingsComponent?: Component
  firstPlayerCopy?: (
    options: Readonly<Record<string, unknown>>,
  ) => BuiltinGameFirstPlayerCopy
  applyChange?: (
    options: Readonly<Record<string, unknown>>,
    key: string,
    value: unknown,
  ) => Record<string, unknown>
  hasHandicap?: (options: Readonly<Record<string, unknown>>) => boolean
}

export interface BuiltinGameDefinition<
  Key extends BuiltinArcadeGameKey = BuiltinArcadeGameKey,
> {
  key: Key
  catalog: BuiltinGameCatalogMetadata
  capabilities: BuiltinGameCapabilities
  presentation: BuiltinGamePresentation
  rules: BuiltinGameRules
}
