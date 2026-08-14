import type { Component } from 'vue'
import type {
  LeaderboardEntry,
  MatchDetail,
  MatchHistoryItem,
  StatsSummary,
} from '../stats'
import type { ArcadeSnapshot, BuiltinArcadeGameKey } from '../types/arcade'

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
  roomShell?: BuiltinGameRoomShellPresentation
  solo?: BuiltinGameSoloPresentation
}

export interface BuiltinGameRoomShellPresentation {
  headerEyebrowSuffix?: (snapshot: ArcadeSnapshot) => string
  headerTitle?: (snapshot: ArcadeSnapshot) => string
  statsMode?: (snapshot: ArcadeSnapshot) => string | undefined
  activeExitDescription?: string
  abandonLabel?: string
  finishedLabel?: string
  rematchLabel?: string
}

export interface BuiltinGameSoloMetric {
  label: string
  value: string
}

export interface BuiltinGameSoloContent {
  category: string
  kicker: string
  title: string
  description: string
  button: string
  features: readonly string[]
  metrics: readonly BuiltinGameSoloMetric[]
  stages: readonly string[]
  recordNote: string
}

export interface BuiltinGameSoloPresentation {
  icon: Component
  accent: string
  hasRuleSettings?: boolean
  content: (
    options: Readonly<Record<string, unknown>>,
  ) => BuiltinGameSoloContent
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

export interface BuiltinGameLeaderboardFilter {
  label: string
  mode: string
  variant?: string
}

export interface BuiltinGameStatsSummaryItem {
  value: string | number
  label: string
}

export interface BuiltinGameMatchDetailMetric {
  status: 'success' | 'failed'
  label: string
  value: string
  note?: string
}

export interface BuiltinGameMatchDetailSection {
  title: string
  metrics: readonly BuiltinGameMatchDetailMetric[]
}

export interface BuiltinGameStatsPresentation {
  defaultMode?: string
  defaultVariant?: (mode: string | undefined) => string | undefined
  titleSuffix?: (mode: string | undefined, variant: string | undefined) => string
  description: string
  filters?: readonly BuiltinGameLeaderboardFilter[]
  summaryItems: (summary: StatsSummary) => readonly BuiltinGameStatsSummaryItem[]
  summaryComponent?: Component
  showDrawSummary?: boolean
  historyOutcome: (match: MatchHistoryItem) => string
  historyTitle: (match: MatchHistoryItem) => string
  historyMeta: (match: MatchHistoryItem, formattedDate: string) => string
  detailSection?: (match: MatchDetail) => BuiltinGameMatchDetailSection
  detailPlayerRoleLabel?: (role: string) => string
  detailModeLabel?: (match: MatchDetail) => string
  detailWinnerLabel: (match: MatchDetail) => string
  detailNote: (match: MatchDetail) => string
}

export interface BuiltinGameLeaderboardPresentation {
  defaultMode?: string
  defaultVariant?: (mode: string | undefined) => string | undefined
  titleSuffix?: (mode: string | undefined, variant: string | undefined) => string
  description: string
  filters?: readonly BuiltinGameLeaderboardFilter[]
  entryDetail: (entry: LeaderboardEntry) => string
  entryScore: (entry: LeaderboardEntry) => string
  note: string
}

export interface BuiltinGameRecords {
  leaderboard?: BuiltinGameLeaderboardPresentation
  stats?: BuiltinGameStatsPresentation
  matchDetailComponent?: Component
  modeFromRules?: (
    options: Readonly<Record<string, unknown>>,
  ) => string | undefined
}

export interface BuiltinGameDefinition<
  Key extends BuiltinArcadeGameKey = BuiltinArcadeGameKey,
> {
  key: Key
  catalog: BuiltinGameCatalogMetadata
  capabilities: BuiltinGameCapabilities
  presentation: BuiltinGamePresentation
  rules: BuiltinGameRules
  records?: BuiltinGameRecords
}
