import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { emitWithAck, socket, type AckResponse } from '../socket'
import type {
  ArcadeGameKey,
  ArcadeLobbyRoom,
  ArcadeSnapshot,
} from '../types/arcade'

interface StoredArcadeSession {
  gameKey: ArcadeGameKey
  roomCode: string
  playerId: string
  resumeToken: string
}

const SESSION_KEY = 'gamehall:arcade-session'

function readSession(): StoredArcadeSession | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    return raw ? (JSON.parse(raw) as StoredArcadeSession) : null
  } catch {
    return null
  }
}

export const useArcadeStore = defineStore('arcade', () => {
  const snapshot = ref<ArcadeSnapshot | null>(null)
  const availableRooms = ref<ArcadeLobbyRoom[]>([])
  const busy = ref(false)
  const error = ref<string | null>(null)
  const session = ref<StoredArcadeSession | null>(readSession())
  let initialized = false

  const resumableGame = computed(() =>
    snapshot.value === null ? session.value?.gameKey ?? null : null,
  )
  const resumableRoomCode = computed(() =>
    snapshot.value === null ? session.value?.roomCode ?? null : null,
  )

  function init() {
    if (initialized) return
    initialized = true
    socket.on('connect', async () => {
      if (session.value && !snapshot.value) await resume()
    })
    socket.on('arcade:lobby', (rooms: ArcadeLobbyRoom[]) => {
      availableRooms.value = rooms
    })
    socket.on('arcade:snapshot', (next: ArcadeSnapshot) => {
      if (!snapshot.value || next.revision >= snapshot.value.revision) {
        snapshot.value = next
      }
    })
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

  async function createRoom(
    gameKey: ArcadeGameKey,
    name: string,
    options: Record<string, unknown> = {},
  ) {
    const response = await perform('arcade:create', {
      game_key: gameKey,
      name,
      options,
    })
    if (response?.roomCode && response.playerId && response.resumeToken) {
      saveSession({
        gameKey,
        roomCode: response.roomCode,
        playerId: response.playerId,
        resumeToken: response.resumeToken,
      })
      return true
    }
    return false
  }

  async function joinRoom(
    gameKey: ArcadeGameKey,
    roomCode: string,
    name: string,
  ) {
    const response = await perform('arcade:join', {
      game_key: gameKey,
      room_code: roomCode.trim().toUpperCase(),
      name,
    })
    if (response?.roomCode && response.playerId && response.resumeToken) {
      saveSession({
        gameKey,
        roomCode: response.roomCode,
        playerId: response.playerId,
        resumeToken: response.resumeToken,
      })
    }
  }

  async function resume() {
    if (!session.value) return
    const response = await perform('arcade:resume', {
      room_code: session.value.roomCode,
      token: session.value.resumeToken,
    })
    if (!response) {
      clearSession()
      error.value = null
    }
  }

  async function leaveRoom() {
    const response = await perform('arcade:leave')
    if (response) {
      snapshot.value = null
      if (!response.seatPreserved) clearSession()
    }
  }

  async function startGame() {
    await perform('arcade:start')
  }

  async function action(
    actionName: string,
    payload: Record<string, unknown> = {},
  ) {
    await perform('arcade:action', { action: actionName, payload })
  }

  async function restartGame() {
    await perform('arcade:restart')
  }

  async function returnToRoom() {
    if (session.value && !snapshot.value) await resume()
  }

  function saveSession(next: StoredArcadeSession) {
    session.value = next
    localStorage.setItem(SESSION_KEY, JSON.stringify(next))
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
    busy.value = false
    error.value = null
    clearSession()
  }

  return {
    snapshot,
    availableRooms,
    busy,
    error,
    resumableGame,
    resumableRoomCode,
    init,
    createRoom,
    joinRoom,
    leaveRoom,
    startGame,
    action,
    restartGame,
    returnToRoom,
    clearError,
    resetForLogout,
  }
})
