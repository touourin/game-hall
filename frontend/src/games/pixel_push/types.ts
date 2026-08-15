export type PixelPushStage = 'countdown' | 'active' | 'round_result'
export type PixelPushMapKey = 'moon_station' | 'cross_bridge' | 'pulse_factory'

export interface PixelPushEvent {
  id: number
  tick: number
  kind: string
  actorId: string | null
  targetId: string | null
  value: number | null
}

export interface PixelPushPlayerState {
  id: string
  name?: string
  seat?: number
  color?: string
  x: number
  y: number
  vx: number
  vy: number
  facingX: number
  facingY: number
  balance: number
  alive: boolean
  dashing: boolean
  bracing: boolean
  dashCooldownTicks: number
  disconnectTicks: number
  lastInputSequence?: number
  roundWins?: number
  eliminations?: number
  ringOuts?: number
}

export interface PixelPushGameState {
  tick: number
  tickRate: number
  stage: PixelPushStage
  stageTicksRemaining: number
  roundTicksRemaining: number
  roundNumber: number
  roundsToWin: number
  currentMap: PixelPushMapKey
  mapSequence: PixelPushMapKey[]
  shrinkProgress: number
  roundWinnerId: string | null
  matchWinnerId: string | null
  frozen: boolean
  world: {
    width: number
    height: number
    playerRadius: number
  }
  players: PixelPushPlayerState[]
  roundWins: Record<string, number>
  events: PixelPushEvent[]
  selfInputSequence: number
}

export interface PixelPushFrame {
  roomCode: string
  revision: number
  tick: number
  stage: PixelPushStage
  stageTicksRemaining: number
  roundTicksRemaining: number
  roundNumber: number
  currentMap: PixelPushMapKey
  shrinkProgress: number
  roundWinnerId: string | null
  matchWinnerId: string | null
  roundWins: Record<string, number>
  frozen: boolean
  players: PixelPushPlayerState[]
  events: PixelPushEvent[]
}

export const INPUT_UP = 1
export const INPUT_DOWN = 2
export const INPUT_LEFT = 4
export const INPUT_RIGHT = 8
export const INPUT_DASH = 16
export const INPUT_BRACE = 32
