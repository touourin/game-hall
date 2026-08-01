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

describe('Avalon room store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('clears a stale room snapshot when reconnecting cannot resume it', async () => {
    localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        roomCode: 'SA6E',
        playerId: 'player-1',
        resumeToken: 'resume-token-for-player-1',
      }),
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
