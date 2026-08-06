export type BuiltinArcadeGameKey =
  | 'avalon'
  | 'gomoku'
  | 'xiangqi'
  | 'go'
  | 'poker'
  | 'doudizhu'
  | 'junqi'
  | 'reaction'
  | 'schulte'
  | 'minesweeper'
  | 'hanoi'
  | 'monopoly'

export type PluginArcadeGameKey = `plugin-${string}`
export type ArcadeGameKey = BuiltinArcadeGameKey | PluginArcadeGameKey

export interface GameCatalogItem {
  key: ArcadeGameKey
  name: string
  players: string
  description: string
}

export interface ArcadeLobbyRoom {
  roomCode: string
  gameKey: ArcadeGameKey
  gameName: string
  hostName: string
  hostAvatarUrl?: string | null
  playerCount: number
  maxPlayers: number
  options: Record<string, unknown>
  allowsGuests?: boolean
  statsEligible?: boolean
  phase?: ArcadePhase
  cleanupAvailable?: boolean
  allHumansOffline?: boolean
}

export interface ArcadePlayer {
  id: string
  name: string
  avatarUrl?: string | null
  isBot?: boolean
  isGuest?: boolean
  seat: number
  connected: boolean
  disconnectForfeitAt?: string | null
  disconnectForfeited?: boolean
  leftRoom?: boolean
  isHost: boolean
}

export interface ArcadeChatMessage {
  id: string
  senderId: string
  senderName: string
  senderAvatarUrl?: string | null
  content: string
  createdAt: string
}

export interface ArcadeGameRequest {
  kind: 'undo' | 'draw' | 'end_table'
  requesterId: string
  requesterName: string
  isMine: boolean
  hasApproved?: boolean
  canRespond?: boolean
  approvedPlayerIds?: string[]
  approvalCount?: number
  requiredApprovalCount?: number
}

export interface ArcadeSnapshot {
  revision: number
  roomCode: string
  gameKey: ArcadeGameKey
  gameName: string
  phase: ArcadePhase
  statsEligible?: boolean
  hostTransferAt?: string | null
  options: Record<string, unknown>
  hostId: string
  self: { id: string; accountId?: string; name: string; seat: number; avatarUrl?: string | null; isGuest?: boolean }
  players: ArcadePlayer[]
  requiredPlayers: number
  minimumPlayers?: number
  roundNumber: number
  winner: string | null
  winnerPlayerIds: string[]
  winReason: string | null
  actions: {
    canStart: boolean
    canRestart: boolean
    canAct: boolean
    canKickPlayers: boolean
    canDissolve: boolean
    canEditRules: boolean
    canRequestUndo: boolean
    canRequestDraw: boolean
    canRequestEndTable?: boolean
    canResolveRequest: boolean
  }
  rematchReadyPlayerIds: string[]
  request: ArcadeGameRequest | null
  chat: {
    maxLength: number
    messages: ArcadeChatMessage[]
  }
  game: Record<string, unknown>
}

export type AvalonArcadeSnapshot = Omit<ArcadeSnapshot, 'gameKey' | 'game'> & {
  gameKey: 'avalon'
  game: import('./avalon').RoomSnapshot
}

export function isAvalonArcadeSnapshot(
  snapshot: ArcadeSnapshot,
): snapshot is ArcadeSnapshot & AvalonArcadeSnapshot {
  return snapshot.gameKey === 'avalon'
}

export type ArcadePhase =
  | 'lobby'
  | 'setup'
  | 'bidding'
  | 'playing'
  | 'between_hands'
  | 'scoring'
  | 'finished'
  | 'role_reveal'
  | 'team_building'
  | 'team_voting'
  | 'mission_voting'
  | 'round_result'
  | 'lady_select'
  | 'lady_reveal'
  | 'assassination'
  | 'dagger_grant'
  | 'final_council'
  | 'exile_council_ballot'
  | 'exile_council_assassination_decision'
  | 'exile_council_assassination_target'
