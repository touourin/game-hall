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

const SESSION_KEY = 'gamehall:arcade-session'
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

describe('arcade room store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
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
