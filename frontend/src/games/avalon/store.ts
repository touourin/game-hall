import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { emitWithAck, socket, type AckResponse } from '../../socket'
import type { LobbyRoom, RoomSnapshot } from './types'

interface StoredSession {
  roomCode: string
  playerId: string
  resumeToken: string
}

const SESSION_KEY = 'avalon:current-session'

function readSession(): StoredSession | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    return raw ? (JSON.parse(raw) as StoredSession) : null
  } catch {
    return null
  }
}

export const useRoomStore = defineStore('room', () => {
  const snapshot = ref<RoomSnapshot | null>(null)
  const availableRooms = ref<LobbyRoom[]>([])
  const connected = ref(false)
  const restoring = ref(false)
  const busy = ref(false)
  const error = ref<string | null>(null)
  const session = ref<StoredSession | null>(readSession())
  let initialized = false

  const inRoom = computed(() => snapshot.value !== null)
  const resumableRoomCode = computed(() =>
    snapshot.value === null ? session.value?.roomCode ?? null : null,
  )

  function init() {
    if (initialized) return
    initialized = true

    socket.on('connect', async () => {
      connected.value = true
      if (session.value) {
        await resume()
      }
    })
    socket.on('disconnect', () => {
      connected.value = false
    })
    socket.on('connect_error', () => {
      connected.value = false
      error.value = '暂时连接不到游戏服务器'
    })
    socket.on('room:snapshot', (nextSnapshot: RoomSnapshot) => {
      if (
        snapshot.value === null ||
        nextSnapshot.revision >= snapshot.value.revision
      ) {
        snapshot.value = nextSnapshot
      }
    })
    socket.on('lobby:rooms', (nextRooms: LobbyRoom[]) => {
      availableRooms.value = nextRooms
    })
    socket.on('room:kicked', (payload: { message?: string }) => {
      snapshot.value = null
      clearSession()
      error.value = payload.message ?? '你已离开房间'
      window.setTimeout(() => {
        if (!socket.connected) socket.connect()
      }, 250)
    })
    socket.connect()
  }

  async function perform(
    event: string,
    payload: Record<string, unknown> = {},
  ): Promise<AckResponse | null> {
    busy.value = true
    error.value = null
    try {
      const response = await emitWithAck(event, payload)
      if (!response.ok) {
        error.value = response.error ?? '操作没有成功'
        return null
      }
      return response
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : '网络连接异常'
      return null
    } finally {
      busy.value = false
    }
  }

  async function createRoom(name: string) {
    const response = await perform('room:create', { name })
    if (response?.roomCode && response.playerId && response.resumeToken) {
      saveSession({
        roomCode: response.roomCode,
        playerId: response.playerId,
        resumeToken: response.resumeToken,
      })
    }
  }

  async function joinRoom(roomCode: string, name: string) {
    const response = await perform('room:join', {
      room_code: roomCode.trim().toUpperCase(),
      name,
    })
    if (response?.roomCode && response.playerId && response.resumeToken) {
      saveSession({
        roomCode: response.roomCode,
        playerId: response.playerId,
        resumeToken: response.resumeToken,
      })
    }
  }

  async function resume() {
    if (!session.value) return
    restoring.value = true
    const response = await perform('room:resume', {
      room_code: session.value.roomCode,
      token: session.value.resumeToken,
    })
    if (!response) {
      clearSession()
    }
    restoring.value = false
  }

  async function leaveRoom() {
    const response = await perform('room:leave')
    if (response) {
      snapshot.value = null
      if (!response.seatPreserved) {
        clearSession()
      }
    }
  }

  async function returnToRoom() {
    if (!session.value || snapshot.value) return
    await resume()
  }

  function saveSession(nextSession: StoredSession) {
    session.value = nextSession
    localStorage.setItem(SESSION_KEY, JSON.stringify(nextSession))
  }

  function clearSession() {
    session.value = null
    localStorage.removeItem(SESSION_KEY)
  }

  function clearError() {
    error.value = null
  }

  function resetForLogout() {
    snapshot.value = null
    connected.value = false
    restoring.value = false
    busy.value = false
    error.value = null
    clearSession()
  }

  return {
    snapshot,
    availableRooms,
    connected,
    restoring,
    busy,
    error,
    inRoom,
    resumableRoomCode,
    init,
    perform,
    createRoom,
    joinRoom,
    leaveRoom,
    returnToRoom,
    clearError,
    resetForLogout,
  }
})
