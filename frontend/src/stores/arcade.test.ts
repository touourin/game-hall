import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ArcadeSnapshot } from '../types/arcade'

const socketMocks = vi.hoisted(() => ({
  emitWithAck: vi.fn(),
  socket: {
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

  it('discovers an active room from another device after connecting', async () => {
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

  it('clears a detached device when another device exits the room', () => {
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
})
