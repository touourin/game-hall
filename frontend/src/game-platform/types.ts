import type { Component } from 'vue'
import type {
  LeaderboardEntry,
  MatchDetail,
  MatchHistoryItem,
  StatsSummary,
} from '../stats'
import type {
  ArcadeGameKey,
  ArcadeSnapshot,
  BuiltinArcadeGameKey,
} from '../types/arcade'

export type GameSource = 'official' | 'third_party'
export type GameAvailability = 'enabled' | 'deprecated'

export type BuiltinGameRoomLayout = 'standard' | 'wide' | 'immersive'
export type BuiltinGameSkinKind = 'board' | 'cards'

export interface BuiltinGameArtwork {
  dark: string
  light: string
}

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
  artwork?: BuiltinGameArtwork
}

export function gamePlayerLabel(
  players: BuiltinGameCatalogMetadata['players'],
): string {
  if (players.label) return players.label
  return players.min === players.max
    ? `${players.min} 人`
    : `${players.min}–${players.max} 人`
}

export const builtinGamePlayerLabel = gamePlayerLabel

export interface BuiltinGameCapabilities {
  undo: boolean
  draw: boolean
  guests: boolean
  spectators: boolean
  spectatorFrames: boolean
  firstPlayer: boolean
  replay: boolean
  ai: boolean
}

export interface BuiltinGamePresentation {
  component: Component
  roomLayout: BuiltinGameRoomLayout
  skinKind: BuiltinGameSkinKind | null
  launcher?: BuiltinGameLauncherPresentation
  roomShell?: BuiltinGameRoomShellPresentation
  solo?: BuiltinGameSoloPresentation
}

export interface BuiltinGameLauncherPresentation {
  kicker: string
  title: string
  description: string
  accent: string
  glow: string
}

export interface BuiltinGameRoomShellPresentation {
  headerDetailsComponent?: Component
  headerActionsComponent?: Component
  ruleActionsComponent?: Component
  lobbyComponent?: Component
  headerEyebrowSuffix?: (snapshot: ArcadeSnapshot) => string
  headerTitle?: (snapshot: ArcadeSnapshot) => string
  statsMode?: (snapshot: ArcadeSnapshot) => string | undefined
  waitingMessage?: (snapshot: ArcadeSnapshot) => string | null
  handlesResult?: boolean
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

export type BuiltinGameRuleSettingOption = readonly [
  value: string | number | boolean,
  label: string,
  description?: string,
]

export interface BuiltinGameRuleSettingGroup {
  key: string
  title: string
  description: string
  control: 'cards' | 'segmented'
  columns?: 2 | 3 | 5 | 6
  visibleWhen?: readonly [key: string, value: string | number | boolean]
  options: readonly BuiltinGameRuleSettingOption[]
}

export interface BuiltinGameRules {
  defaults: Readonly<Record<string, unknown>>
  labels: (options: Readonly<Record<string, unknown>>) => string[]
  settingsGroups?: readonly BuiltinGameRuleSettingGroup[]
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
  scoreKind?: 'outcome' | 'time_trial' | 'high_score'
  leaderboard?: BuiltinGameLeaderboardPresentation
  stats?: BuiltinGameStatsPresentation
  matchDetailComponent?: Component
  modeFromRules?: (
    options: Readonly<Record<string, unknown>>,
  ) => string | undefined
}

export interface GamePluginMetadata {
  version: string
  author: string
  license: string
  directory: string
}

export interface GameRegistration<
  Key extends ArcadeGameKey = ArcadeGameKey,
> {
  key: Key
  source: GameSource
  availability: GameAvailability
  plugin?: GamePluginMetadata
  catalog: BuiltinGameCatalogMetadata
  capabilities: BuiltinGameCapabilities
  presentation: BuiltinGamePresentation
  rules: BuiltinGameRules
  records?: BuiltinGameRecords
}

export type BuiltinGameDefinition<
  Key extends BuiltinArcadeGameKey = BuiltinArcadeGameKey,
> = Omit<GameRegistration<Key>, 'source' | 'availability' | 'plugin'>
