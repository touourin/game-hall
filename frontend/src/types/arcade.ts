export type ArcadeGameKey = 'gomoku' | 'xiangqi' | 'go' | 'doudizhu'

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
}

export interface ArcadePlayer {
  id: string
  name: string
  seat: number
  connected: boolean
  isHost: boolean
}

export interface ArcadeSnapshot {
  revision: number
  roomCode: string
  gameKey: ArcadeGameKey
  gameName: string
  phase: 'lobby' | 'bidding' | 'playing' | 'finished'
  hostId: string
  self: { id: string; name: string; seat: number }
  players: ArcadePlayer[]
  requiredPlayers: number
  winner: string | null
  winnerPlayerIds: string[]
  winReason: string | null
  actions: {
    canStart: boolean
    canRestart: boolean
    canAct: boolean
  }
  game: Record<string, unknown>
}
