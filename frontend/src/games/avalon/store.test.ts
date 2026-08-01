import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { RoomSnapshot } from './types'

const socketMocks = vi.hoisted(() => ({
  emitWithAck: vi.fn(),
  socket: {
    connected: true,
    connect: vi.fn(),
    on: vi.fn(),
  },
}))

vi.mock('../../socket', () => socketMocks)

import { useRoomStore } from './store'

const SESSION_KEY = 'avalon:current-session'
const storedSession = {
  roomCode: 'SA6E',
  playerId: 'player-1',
  resumeToken: 'resume-token-for-player-1',
}

describe('Avalon room store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('clears a stale room snapshot when reconnecting cannot resume it', async () => {
    localStorage.setItem(
      SESSION_KEY,
      JSON.stringify(storedSession),
    )
    socketMocks.emitWithAck.mockResolvedValue({
      ok: false,
      error: '房间不存在',
    })
    const room = useRoomStore()
    room.snapshot = { roomCode: 'SA6E' } as RoomSnapshot
    room.init()
    const connectHandler = socketMocks.socket.on.mock.calls.find(
      ([event]) => event === 'connect',
    )?.[1] as (() => Promise<void>) | undefined

    expect(connectHandler).toBeTypeOf('function')
    await connectHandler?.()

    expect(room.snapshot).toBeNull()
    expect(room.resumableRoomCode).toBeNull()
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('lets any logged-in client clean an eligible room', async () => {
    socketMocks.emitWithAck.mockResolvedValue({ ok: true })
    const room = useRoomStore()

    expect(await room.cleanupRoom('OLD1')).toBe(true)
    expect(socketMocks.emitWithAck).toHaveBeenCalledWith('room:cleanup', {
      room_code: 'OLD1',
    })
  })

  it('dissolves the current room and clears its saved session', async () => {
    localStorage.setItem(SESSION_KEY, JSON.stringify(storedSession))
    socketMocks.emitWithAck.mockResolvedValue({ ok: true })
    const room = useRoomStore()
    room.snapshot = { roomCode: 'SA6E' } as RoomSnapshot

    expect(await room.dissolveRoom()).toBe(true)
    expect(socketMocks.emitWithAck).toHaveBeenCalledWith('room:dissolve', {})
    expect(room.snapshot).toBeNull()
    expect(localStorage.getItem(SESSION_KEY)).toBeNull()
  })

  it('returns a guest to the lobby when the host dissolves the room', () => {
    localStorage.setItem(SESSION_KEY, JSON.stringify(storedSession))
    const room = useRoomStore()
    room.snapshot = { roomCode: 'SA6E' } as RoomSnapshot
    room.init()
    const closedHandler = socketMocks.socket.on.mock.calls.find(
      ([event]) => event === 'room:closed',
    )?.[1] as ((payload: { message?: string; silent?: boolean }) => void) | undefined

    expect(closedHandler).toBeTypeOf('function')
    closedHandler?.({ message: '房主已解散房间' })

    expect(room.snapshot).toBeNull()
    expect(room.resumableRoomCode).toBeNull()
    expect(room.error).toBe('房主已解散房间')
  })

  it('clears a temporary connection error after reconnecting', async () => {
    const room = useRoomStore()
    room.error = '暂时连接不到游戏服务器'
    room.init()
    const connectHandler = socketMocks.socket.on.mock.calls.find(
      ([event]) => event === 'connect',
    )?.[1] as (() => Promise<void>) | undefined

    await connectHandler?.()

    expect(room.connected).toBe(true)
    expect(room.error).toBeNull()
  })
})
