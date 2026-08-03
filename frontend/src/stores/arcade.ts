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
  resumeToken?: string
}

interface RoomClosurePayload {
  roomCode?: string
  message?: string
  silent?: boolean
}

const SESSION_KEY = 'game-hall:arcade-session'
const LEGACY_SESSION_KEY = 'gamehall:arcade-session'
const LEGACY_AVALON_SESSION_KEY = 'avalon:current-session'

function readSession(): StoredArcadeSession | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    if (raw) return JSON.parse(raw) as StoredArcadeSession

    const legacyRaw = localStorage.getItem(LEGACY_SESSION_KEY)
    if (legacyRaw) {
      const session = JSON.parse(legacyRaw) as StoredArcadeSession
      localStorage.setItem(SESSION_KEY, legacyRaw)
      localStorage.removeItem(LEGACY_SESSION_KEY)
      return session
    }

    const avalonRaw = localStorage.getItem(LEGACY_AVALON_SESSION_KEY)
    if (!avalonRaw) return null
    const legacyAvalon = JSON.parse(avalonRaw) as Omit<StoredArcadeSession, 'gameKey'>
    const session: StoredArcadeSession = { ...legacyAvalon, gameKey: 'avalon' }
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
    localStorage.removeItem(LEGACY_AVALON_SESSION_KEY)
    return session
  } catch {
    return null
  }
}

export const useArcadeStore = defineStore('arcade', () => {
  const snapshot = ref<ArcadeSnapshot | null>(null)
  const availableRooms = ref<ArcadeLobbyRoom[]>([])
  const connected = ref(false)
  const busy = ref(false)
  const error = ref<string | null>(null)
  const session = ref<StoredArcadeSession | null>(readSession())
  let initialized = false

  const activeGame = computed(() => snapshot.value?.gameKey ?? session.value?.gameKey ?? null)
  const activeRoomCode = computed(() => snapshot.value?.roomCode ?? session.value?.roomCode ?? null)
  const resumableGame = computed(() => session.value?.gameKey ?? null)
  const resumableRoomCode = computed(() => session.value?.roomCode ?? null)

  function init() {
    if (initialized) return
    initialized = true
    connected.value = socket.connected
    socket.on('connect', async () => {
      connected.value = true
      error.value = null
      if (session.value?.resumeToken && await resume()) return
      await syncActiveRoom()
    })
    socket.on('disconnect', () => {
      connected.value = false
    })
    socket.on('connect_error', () => {
      connected.value = false
      error.value = '暂时连接不到游戏服务器'
    })
    socket.on('arcade:lobby', (rooms: ArcadeLobbyRoom[]) => {
      availableRooms.value = rooms
    })
    socket.on('arcade:snapshot', (next: ArcadeSnapshot) => {
      if (!snapshot.value || next.revision >= snapshot.value.revision) {
        snapshot.value = next
      }
    })
    socket.on('arcade:kicked', (payload: RoomClosurePayload) => {
      handleRoomClosure(payload, '你已被移出房间')
    })
    socket.on('arcade:closed', (payload: RoomClosurePayload) => {
      handleRoomClosure(payload, '房间已经解散')
    })
    socket.on('arcade:left', (payload: RoomClosurePayload) => {
      handleRoomClosure(payload, '你已退出房间')
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
      return true
    }
    return false
  }

  async function resume() {
    if (!session.value?.resumeToken) return false
    const response = await perform('arcade:resume', {
      room_code: session.value.roomCode,
      token: session.value.resumeToken,
    })
    if (!response) {
      snapshot.value = null
      clearSession()
      error.value = null
      return false
    }
    return true
  }

  async function syncActiveRoom() {
    const response = await perform('arcade:active')
    if (!response) return false
    if (
      response.activeRoom
      && response.roomCode
      && response.gameKey
      && response.playerId
    ) {
      saveSession({
        gameKey: response.gameKey as ArcadeGameKey,
        roomCode: response.roomCode,
        playerId: response.playerId,
      })
      return true
    }
    if (!snapshot.value) clearSession()
    return false
  }

  async function detachRoom() {
    const response = await perform('arcade:detach')
    if (response) snapshot.value = null
    return Boolean(response)
  }

  async function leaveRoom() {
    const response = await perform('arcade:leave')
    if (response) {
      snapshot.value = null
      clearSession()
    }
    return Boolean(response)
  }

  async function abandonRoom() {
    const response = await perform('arcade:abandon')
    if (response) {
      snapshot.value = null
      clearSession()
    }
    return Boolean(response)
  }

  async function cleanupRoom(roomCode: string) {
    const response = await perform('arcade:cleanup', {
      room_code: roomCode,
    })
    if (response && session.value?.roomCode === roomCode) {
      snapshot.value = null
      clearSession()
    }
    return Boolean(response)
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

  async function actionWithResult(
    actionName: string,
    payload: Record<string, unknown> = {},
  ) {
    return Boolean(await perform('arcade:action', { action: actionName, payload }))
  }

  async function rapidAction(
    actionName: string,
    payload: Record<string, unknown> = {},
  ): Promise<boolean> {
    error.value = null
    try {
      const response = await emitWithAck('arcade:action', {
        action: actionName,
        payload,
      })
      if (!response.ok) {
        error.value = response.error ?? '操作没有成功'
        return false
      }
      return true
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : '网络连接异常'
      return false
    }
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

  async function requestGameAction(kind: 'undo' | 'draw' | 'end_table') {
    return Boolean(await perform('arcade:request', { kind }))
  }

  async function resolveGameRequest(accept: boolean) {
    return Boolean(await perform('arcade:request:resolve', { accept }))
  }

  async function updateRules(options: Record<string, unknown>) {
    return Boolean(await perform('arcade:rules:update', { options }))
  }

  async function returnToRoom() {
    if (snapshot.value) return true
    if (session.value?.resumeToken && await resume()) return true
    return syncActiveRoom()
  }

  function saveSession(next: StoredArcadeSession) {
    session.value = next
    localStorage.setItem(SESSION_KEY, JSON.stringify(next))
    localStorage.removeItem(LEGACY_SESSION_KEY)
    localStorage.removeItem(LEGACY_AVALON_SESSION_KEY)
  }

  function clearSession() {
    session.value = null
    localStorage.removeItem(SESSION_KEY)
    localStorage.removeItem(LEGACY_SESSION_KEY)
    localStorage.removeItem(LEGACY_AVALON_SESSION_KEY)
  }

  function clearError() {
    error.value = null
  }

  function handleRoomClosure(
    payload: RoomClosurePayload,
    fallbackMessage: string,
  ) {
    const currentRoomCode = snapshot.value?.roomCode ?? session.value?.roomCode
    if (
      payload.roomCode
      && currentRoomCode
      && payload.roomCode !== currentRoomCode
    ) return
    snapshot.value = null
    clearSession()
    error.value = payload.silent ? null : (payload.message ?? fallbackMessage)
  }

  function resetForLogout() {
    snapshot.value = null
    connected.value = false
    busy.value = false
    error.value = null
    clearSession()
  }

  return {
    snapshot,
    availableRooms,
    connected,
    busy,
    error,
    activeGame,
    activeRoomCode,
    resumableGame,
    resumableRoomCode,
    init,
    createRoom,
    joinRoom,
    syncActiveRoom,
    detachRoom,
    leaveRoom,
    abandonRoom,
    cleanupRoom,
    startGame,
    action,
    actionWithResult,
    rapidAction,
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
