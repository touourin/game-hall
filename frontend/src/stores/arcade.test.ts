import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type {
  ArcadeRealtimeFrame,
  ArcadeSnapshot,
  ArcadeSpectatorFrame,
} from '../types/arcade'

const socketMocks = vi.hoisted(() => ({
  emitWithAck: vi.fn(),
  socket: {
    emit: vi.fn(),
    on: vi.fn(),
  },
}))

vi.mock('../socket', () => socketMocks)

import { useArcadeStore } from './arcade'

const SESSION_KEY = 'game-hall:arcade-session'
const LEGACY_SESSION_KEY = 'gamehall:arcade-session'
const LEGACY_AVALON_SESSION_KEY = 'avalon:current-session'
const storedSession = {
  gameKey: 'xiangqi',
  roomCode: 'TEST',
  playerId: 'player-1',
  resumeToken: 'resume-token-for-player-1',
}

function connectHandler(): (() => Promise<void>) | undefined {
  return socketMocks.socket.on.mock.calls.find(
    ([event]) => event === 'connect',
  )?.[1] as (() => Promise<void>) | undefined
}

function socketHandler<T>(eventName: string): ((payload: T) => void) | undefined {
  return socketMocks.socket.on.mock.calls.find(
    ([event]) => event === eventName,
  )?.[1] as ((payload: T) => void) | undefined
}

describe('arcade room store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('migrates the old game-hall room session key', () => {
    localStorage.setItem(LEGACY_SESSION_KEY, JSON.stringify(storedSession))

    const arcade = useArcadeStore()

    expect(arcade.resumableRoomCode).toBe('TEST')
    expect(localStorage.getItem(SESSION_KEY)).toBe(JSON.stringify(storedSession))
    expect(localStorage.getItem(LEGACY_SESSION_KEY)).toBeNull()
  })

  it('migrates the former Avalon seat into the unified room session', () => {
    const legacyAvalon = {
      roomCode: 'AVLN',
      playerId: 'arthur',
      resumeToken: 'resume-token-for-arthur',
    }
    localStorage.setItem(
      LEGACY_AVALON_SESSION_KEY,
      JSON.stringify(legacyAvalon),
    )

    const arcade = useArcadeStore()

    expect(arcade.resumableGame).toBe('avalon')
    expect(arcade.resumableRoomCode).toBe('AVLN')
    expect(JSON.parse(localStorage.getItem(SESSION_KEY) ?? '{}')).toEqual({
      ...legacyAvalon,
      gameKey: 'avalon',
    })
    expect(localStorage.getItem(LEGACY_AVALON_SESSION_KEY)).toBeNull()
  })

  it('resumes the room after reconnecting even while an old snapshot is visible', async () => {
    localStorage.setItem(SESSION_KEY, JSON.stringify(storedSession))
    socketMocks.emitWithAck.mockResolvedValue({
      ok: true,
      roomCode: 'TEST',
      gameKey: 'xiangqi',
      playerId: 'player-1',
    })
    const arcade = useArcadeStore()
    arcade.snapshot = { roomCode: 'TEST', revision: 8 } as ArcadeSnapshot
    arcade.init()

    expect(connectHandler()).toBeTypeOf('function')
    await connectHandler()?.()

    expect(socketMocks.emitWithAck).toHaveBeenCalledWith('arcade:resume', {
      room_code: 'TEST',
      token: storedSession.resumeToken,
    })
    expect(arcade.snapshot?.roomCode).toBe('TEST')
    expect(arcade.resumableRoomCode).toBe('TEST')
    expect(arcade.activeRoomCode).toBe('TEST')
  })

  it('reports a successful routed room join', async () => {
    socketMocks.emitWithAck.mockResolvedValue({
      ok: true,
      roomCode: 'A1B2',
      playerId: 'player-2',
      resumeToken: 'resume-token-for-player-2',
    })
    const arcade = useArcadeStore()

    expect(await arcade.joinRoom('junqi', 'a1b2')).toBe(true)
    expect(arcade.activeGame).toBe('junqi')
    expect(arcade.activeRoomCode).toBe('A1B2')
  })

  it('sends a custom room name when creating a room', async () => {
    socketMocks.emitWithAck.mockResolvedValue({
      ok: true,
      roomCode: 'NAME',
      playerId: 'player-name',
      resumeToken: 'resume-token-for-player-name',
    })
    const arcade = useArcadeStore()

    expect(await arcade.createRoom('avalon', {}, '  暗流议会  ')).toBe(true)
    expect(socketMocks.emitWithAck).toHaveBeenCalledWith('arcade:create', {
      game_key: 'avalon',
      options: {},
      room_name: '暗流议会',
    })
  })

  it('discovers the existing room after a new login connects', async () => {
    socketMocks.emitWithAck.mockResolvedValue({
      ok: true,
      activeRoom: true,
      roomCode: 'SYNC',
      gameKey: 'reaction',
      playerId: 'player-sync',
    })
    const arcade = useArcadeStore()
    arcade.init()

    await connectHandler()?.()

    expect(socketMocks.emitWithAck).toHaveBeenCalledWith('arcade:active', {})
    expect(arcade.activeGame).toBe('reaction')
    expect(arcade.activeRoomCode).toBe('SYNC')
  })

  it('keeps recovery state on temporary return and clears it on abandon', async () => {
    localStorage.setItem(SESSION_KEY, JSON.stringify(storedSession))
    socketMocks.emitWithAck.mockResolvedValue({ ok: true, seatPreserved: true })
    const arcade = useArcadeStore()

    expect(await arcade.detachRoom()).toBe(true)
    expect(arcade.activeRoomCode).toBe('TEST')

    socketMocks.emitWithAck.mockResolvedValue({ ok: true, seatPreserved: false })
    expect(await arcade.abandonRoom()).toBe(true)
    expect(arcade.activeRoomCode).toBeNull()
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('clears a detached tab when another tab exits the room', () => {
    localStorage.setItem(SESSION_KEY, JSON.stringify(storedSession))
    const arcade = useArcadeStore()
    arcade.init()

    socketHandler<{ roomCode: string; silent: boolean }>('arcade:left')?.({
      roomCode: 'TEST',
      silent: true,
    })

    expect(arcade.activeRoomCode).toBeNull()
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('clears the stale room screen when reconnecting cannot restore the seat', async () => {
    localStorage.setItem(SESSION_KEY, JSON.stringify(storedSession))
    socketMocks.emitWithAck.mockResolvedValue({
      ok: false,
      error: '没有找到这个房间',
    })
    const arcade = useArcadeStore()
    arcade.snapshot = { roomCode: 'TEST', revision: 8 } as ArcadeSnapshot
    arcade.init()

    await connectHandler()?.()

    expect(arcade.snapshot).toBeNull()
    expect(arcade.resumableRoomCode).toBeNull()
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('cleans an eligible room and forgets its own stale session', async () => {
    localStorage.setItem(SESSION_KEY, JSON.stringify(storedSession))
    socketMocks.emitWithAck.mockResolvedValue({ ok: true })
    const arcade = useArcadeStore()

    expect(await arcade.cleanupRoom('TEST')).toBe(true)
    expect(socketMocks.emitWithAck).toHaveBeenCalledWith('arcade:cleanup', {
      room_code: 'TEST',
    })
    expect(arcade.resumableRoomCode).toBeNull()
  })

  it('sends rapid game actions without locking the whole room interface', async () => {
    socketMocks.emitWithAck.mockResolvedValue({ ok: true })
    const arcade = useArcadeStore()

    const succeeded = await arcade.rapidAction('tap', { value: 1 })

    expect(succeeded).toBe(true)
    expect(arcade.busy).toBe(false)
    expect(socketMocks.emitWithAck).toHaveBeenCalledWith('arcade:action', {
      action: 'tap',
      payload: { value: 1 },
    })
  })

  it('keeps only monotonic realtime frames for the active room', () => {
    const arcade = useArcadeStore()
    arcade.snapshot = {
      roomCode: 'PUSH',
      revision: 5,
      phase: 'playing',
    } as ArcadeSnapshot
    arcade.init()
    const receiveFrame = socketHandler<ArcadeRealtimeFrame>('arcade:frame')

    receiveFrame?.({ roomCode: 'PUSH', revision: 6, tick: 12 })
    receiveFrame?.({ roomCode: 'OTHER', revision: 7, tick: 20 })
    receiveFrame?.({ roomCode: 'PUSH', revision: 8, tick: 11 })

    expect(arcade.realtimeFrame).toEqual({
      roomCode: 'PUSH',
      revision: 6,
      tick: 12,
    })

    socketHandler<ArcadeSnapshot>('arcade:snapshot')?.({
      roomCode: 'PUSH',
      revision: 9,
      phase: 'finished',
    } as ArcadeSnapshot)
    expect(arcade.realtimeFrame).toBeNull()
  })

  it('sends realtime input on the low-latency channel without setting busy', async () => {
    socketMocks.emitWithAck.mockResolvedValue({ ok: true, accepted: true })
    const arcade = useArcadeStore()

    expect(await arcade.realtimeInput(42, 24)).toBe(true)
    expect(arcade.busy).toBe(false)
    expect(socketMocks.emitWithAck).toHaveBeenCalledWith('arcade:input', {
      sequence: 42,
      input_mask: 24,
    })
  })

  it('publishes and accepts fixed-target local game spectator frames', () => {
    const arcade = useArcadeStore()
    arcade.snapshot = {
      roomCode: 'LOCAL',
      gameKey: 'reaction',
      revision: 4,
      roundNumber: 2,
      phase: 'playing',
      self: { id: 'player-1', name: '测试者', seat: 0 },
      viewer: {
        mode: 'player',
        id: 'player-1',
        name: '测试者',
        targetPlayerId: 'player-1',
      },
      spectators: [{
        id: 'watcher-1',
        name: '观众',
        targetPlayerId: 'player-1',
        targetPlayerName: '测试者',
      }],
    } as ArcadeSnapshot

    expect(arcade.publishSpectatorFrame(3, { stage: 'ready' })).toBe(true)
    expect(socketMocks.socket.emit).toHaveBeenCalledWith(
      'arcade:spectator:frame',
      { sequence: 3, state: { stage: 'ready' } },
    )

    arcade.snapshot = {
      ...arcade.snapshot,
      viewer: {
        mode: 'spectator',
        id: 'watcher-1',
        name: '观众',
        targetPlayerId: 'player-1',
      },
    } as ArcadeSnapshot
    arcade.init()
    const receiveFrame = socketHandler<ArcadeSpectatorFrame>(
      'arcade:spectator:frame',
    )
    receiveFrame?.({
      roomCode: 'LOCAL',
      gameKey: 'reaction',
      roundNumber: 2,
      targetPlayerId: 'player-1',
      sequence: 4,
      state: { stage: 'waiting' },
    })
    receiveFrame?.({
      roomCode: 'LOCAL',
      gameKey: 'reaction',
      roundNumber: 2,
      targetPlayerId: 'other-player',
      sequence: 5,
      state: { stage: 'finished' },
    })

    expect(arcade.spectatorFrame?.state).toEqual({ stage: 'waiting' })
    expect(arcade.publishSpectatorFrame(6, { stage: 'ready' })).toBe(false)
  })

  it('enters a fixed first-person watch session and blocks game actions', async () => {
    socketMocks.emitWithAck.mockResolvedValue({
      ok: true,
      roomCode: 'EYES',
      gameKey: 'doudizhu',
      spectatorId: 'watcher-1',
      targetPlayerId: 'player-2',
    })
    const arcade = useArcadeStore()

    expect(await arcade.watchRoom('doudizhu', 'eyes', 'player-2')).toBe(true)
    expect(arcade.isSpectating).toBe(true)
    expect(JSON.parse(localStorage.getItem(SESSION_KEY) ?? '{}')).toEqual({
      mode: 'spectator',
      gameKey: 'doudizhu',
      roomCode: 'EYES',
      targetPlayerId: 'player-2',
    })

    socketMocks.emitWithAck.mockClear()
    expect(await arcade.actionWithResult('play', { cards: ['a'] })).toBe(false)
    expect(socketMocks.emitWithAck).not.toHaveBeenCalled()
    expect(arcade.error).toContain('观战模式')
  })

  it('restores a spectator view after reconnecting', async () => {
    localStorage.setItem(SESSION_KEY, JSON.stringify({
      mode: 'spectator',
      gameKey: 'poker',
      roomCode: 'LOOK',
      targetPlayerId: 'player-3',
    }))
    socketMocks.emitWithAck.mockResolvedValue({
      ok: true,
      roomCode: 'LOOK',
      gameKey: 'poker',
      spectatorId: 'watcher-2',
      targetPlayerId: 'player-3',
    })
    const arcade = useArcadeStore()
    arcade.init()

    await connectHandler()?.()

    expect(socketMocks.emitWithAck).toHaveBeenCalledWith('arcade:watch', {
      game_key: 'poker',
      room_code: 'LOOK',
      target_id: 'player-3',
    })
    expect(arcade.activeRoomCode).toBe('LOOK')
    expect(arcade.isSpectating).toBe(true)
  })

  it('clears the spectator session when the watched room ends', () => {
    localStorage.setItem(SESSION_KEY, JSON.stringify({
      mode: 'spectator',
      gameKey: 'go',
      roomCode: 'VIEW',
      targetPlayerId: 'player-1',
    }))
    const arcade = useArcadeStore()
    arcade.init()

    socketHandler<{ roomCode: string; message: string }>('arcade:watch:ended')?.({
      roomCode: 'VIEW',
      message: '观战结束',
    })

    expect(arcade.activeRoomCode).toBeNull()
    expect(arcade.error).toBe('观战结束')
  })
})
