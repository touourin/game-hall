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
})
