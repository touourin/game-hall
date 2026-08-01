export type ArcadeGameKey =
  | 'gomoku'
  | 'xiangqi'
  | 'go'
  | 'doudizhu'
  | 'junqi'
  | 'reaction'
  | 'schulte'
  | 'hanoi'

export interface GameCatalogItem {
  key: 'avalon' | ArcadeGameKey
  name: string
  players: string
  description: string
}

export interface ArcadeLobbyRoom {
  roomCode: string
  gameKey: ArcadeGameKey
  gameName: string
  hostName: string
  playerCount: number
  maxPlayers: number
  options: Record<string, unknown>
  phase?: 'lobby' | 'setup' | 'bidding' | 'playing' | 'scoring' | 'finished'
  cleanupAvailable?: boolean
  allHumansOffline?: boolean
}

export interface ArcadePlayer {
  id: string
  name: string
  seat: number
  connected: boolean
  isHost: boolean
}

export interface ArcadeChatMessage {
  id: string
  senderId: string
  senderName: string
  content: string
  createdAt: string
}

export interface ArcadeGameRequest {
  kind: 'undo' | 'draw'
  requesterId: string
  requesterName: string
  isMine: boolean
}

export interface ArcadeSnapshot {
  revision: number
  roomCode: string
  gameKey: ArcadeGameKey
  gameName: string
  phase: 'lobby' | 'setup' | 'bidding' | 'playing' | 'scoring' | 'finished'
  hostTransferAt?: string | null
  options: Record<string, unknown>
  hostId: string
  self: { id: string; name: string; seat: number }
  players: ArcadePlayer[]
  requiredPlayers: number
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
