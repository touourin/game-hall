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
      if (session.value) await resume()
    })
    socket.on('arcade:lobby', (rooms: ArcadeLobbyRoom[]) => {
      availableRooms.value = rooms
    })
    socket.on('arcade:snapshot', (next: ArcadeSnapshot) => {
      if (!snapshot.value || next.revision >= snapshot.value.revision) {
        snapshot.value = next
      }
    })
    socket.on('arcade:kicked', (payload: { message?: string }) => {
      snapshot.value = null
      clearSession()
      error.value = payload.message ?? '你已被移出房间'
    })
    socket.on('arcade:closed', (payload: { message?: string; silent?: boolean }) => {
      snapshot.value = null
      clearSession()
      error.value = payload.silent ? null : (payload.message ?? '房间已经解散')
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
    options: Record<string, unknown> = {},
  ) {
    const response = await perform('arcade:create', {
      game_key: gameKey,
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
  ) {
    const response = await perform('arcade:join', {
      game_key: gameKey,
      room_code: roomCode.trim().toUpperCase(),
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
      snapshot.value = null
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
    return Boolean(await perform('arcade:restart'))
  }

  async function kickPlayer(playerId: string) {
    return Boolean(await perform('arcade:kick', { target_id: playerId }))
  }

  async function dissolveRoom() {
    return Boolean(await perform('arcade:dissolve'))
  }

  async function sendChat(content: string) {
    return Boolean(await perform('arcade:chat', { content }))
  }

  async function requestGameAction(kind: 'undo' | 'draw') {
    return Boolean(await perform('arcade:request', { kind }))
  }

  async function resolveGameRequest(accept: boolean) {
    return Boolean(await perform('arcade:request:resolve', { accept }))
  }

  async function updateRules(options: Record<string, unknown>) {
    return Boolean(await perform('arcade:rules:update', { options }))
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
    kickPlayer,
    dissolveRoom,
    sendChat,
    requestGameAction,
    resolveGameRequest,
    updateRules,
    returnToRoom,
    clearError,
    resetForLogout,
  }
})
