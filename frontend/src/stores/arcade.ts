import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { emitWithAck, socket, type AckResponse } from '../socket'
import type {
  ArcadeGameKey,
  ArcadeGameRequestKind,
  ArcadeLobbyRoom,
  ArcadeRealtimeFrame,
  ArcadeSnapshot,
  ArcadeSpectatorFrame,
} from '../types/arcade'

interface StoredArcadeSession {
  gameKey: ArcadeGameKey
  roomCode: string
  mode?: 'player' | 'spectator'
  playerId?: string
  resumeToken?: string
  targetPlayerId?: string
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
  const realtimeFrame = ref<ArcadeRealtimeFrame | null>(null)
  const spectatorFrame = ref<ArcadeSpectatorFrame | null>(null)
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
  const isSpectating = computed(() => (
    snapshot.value?.viewer?.mode === 'spectator'
    || session.value?.mode === 'spectator'
  ))

  function init() {
    if (initialized) return
    initialized = true
    connected.value = socket.connected
    socket.on('connect', async () => {
      connected.value = true
      error.value = null
      if (session.value?.mode === 'spectator' && await resumeWatch()) return
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
        if (
          snapshot.value?.roomCode !== next.roomCode
          || next.phase !== 'playing'
        ) {
          realtimeFrame.value = null
          spectatorFrame.value = null
        }
        snapshot.value = next
      }
    })
    socket.on('arcade:frame', (next: ArcadeRealtimeFrame) => {
      if (snapshot.value?.roomCode !== next.roomCode) return
      if (
        !realtimeFrame.value
        || next.tick >= realtimeFrame.value.tick
      ) realtimeFrame.value = next
    })
    socket.on('arcade:spectator:frame', (next: ArcadeSpectatorFrame) => {
      const current = snapshot.value
      if (
        !current
        || current.viewer?.mode !== 'spectator'
        || current.roomCode !== next.roomCode
        || current.gameKey !== next.gameKey
        || current.roundNumber !== next.roundNumber
        || current.self.id !== next.targetPlayerId
      ) return
      if (
        !spectatorFrame.value
        || spectatorFrame.value.roundNumber !== next.roundNumber
        || next.sequence >= spectatorFrame.value.sequence
      ) spectatorFrame.value = next
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
    socket.on('arcade:watch:ended', (payload: RoomClosurePayload) => {
      handleRoomClosure(payload, '观战已经结束')
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
    roomName = '',
  ) {
    const normalizedRoomName = roomName.trim()
    const response = await perform('arcade:create', {
      game_key: gameKey,
      options,
      ...(normalizedRoomName ? { room_name: normalizedRoomName } : {}),
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

  async function inspectWatchRoom(
    gameKey: ArcadeGameKey,
    roomCode: string,
  ): Promise<ArcadeLobbyRoom | null> {
    const response = await perform('arcade:watch:inspect', {
      game_key: gameKey,
      room_code: roomCode.trim().toUpperCase(),
    })
    return response?.room ?? null
  }

  async function watchRoom(
    gameKey: ArcadeGameKey,
    roomCode: string,
    targetPlayerId: string,
  ): Promise<boolean> {
    const response = await perform('arcade:watch', {
      game_key: gameKey,
      room_code: roomCode.trim().toUpperCase(),
      target_id: targetPlayerId,
    })
    if (
      response?.roomCode
      && response.spectatorId
      && response.targetPlayerId
    ) {
      saveSession({
        mode: 'spectator',
        gameKey,
        roomCode: response.roomCode,
        targetPlayerId: response.targetPlayerId,
      })
      return true
    }
    return false
  }

  async function resumeWatch(): Promise<boolean> {
    const current = session.value
    if (current?.mode !== 'spectator' || !current.targetPlayerId) return false
    const resumed = await watchRoom(
      current.gameKey,
      current.roomCode,
      current.targetPlayerId,
    )
    if (!resumed) {
      snapshot.value = null
      realtimeFrame.value = null
      spectatorFrame.value = null
      clearSession()
      error.value = null
    }
    return resumed
  }

  async function leaveWatch(): Promise<boolean> {
    const response = await perform('arcade:unwatch')
    if (response) {
      snapshot.value = null
      realtimeFrame.value = null
      spectatorFrame.value = null
      clearSession()
    }
    return Boolean(response)
  }

  async function resume() {
    if (!session.value?.resumeToken) return false
    const response = await perform('arcade:resume', {
      room_code: session.value.roomCode,
      token: session.value.resumeToken,
    })
    if (!response) {
      snapshot.value = null
      realtimeFrame.value = null
      spectatorFrame.value = null
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
    if (isSpectating.value) return leaveWatch()
    const response = await perform('arcade:detach')
    if (response) {
      snapshot.value = null
      realtimeFrame.value = null
      spectatorFrame.value = null
    }
    return Boolean(response)
  }

  async function leaveRoom() {
    if (isSpectating.value) return leaveWatch()
    const response = await perform('arcade:leave')
    if (response) {
      snapshot.value = null
      realtimeFrame.value = null
      spectatorFrame.value = null
      clearSession()
    }
    return Boolean(response)
  }

  async function abandonRoom() {
    if (isSpectating.value) return leaveWatch()
    const response = await perform('arcade:abandon')
    if (response) {
      snapshot.value = null
      realtimeFrame.value = null
      spectatorFrame.value = null
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
      realtimeFrame.value = null
      spectatorFrame.value = null
      clearSession()
    }
    return Boolean(response)
  }

  async function startGame() {
    if (rejectSpectatorAction()) return
    await perform('arcade:start')
  }

  async function action(
    actionName: string,
    payload: Record<string, unknown> = {},
  ) {
    if (rejectSpectatorAction()) return
    await perform('arcade:action', { action: actionName, payload })
  }

  async function actionWithResult(
    actionName: string,
    payload: Record<string, unknown> = {},
  ) {
    if (rejectSpectatorAction()) return false
    return Boolean(await perform('arcade:action', { action: actionName, payload }))
  }

  async function rapidAction(
    actionName: string,
    payload: Record<string, unknown> = {},
  ): Promise<boolean> {
    if (rejectSpectatorAction()) return false
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

  async function realtimeInput(
    sequence: number,
    inputMask: number,
  ): Promise<boolean> {
    if (rejectSpectatorAction()) return false
    try {
      const response = await emitWithAck('arcade:input', {
        sequence,
        input_mask: inputMask,
      })
      if (!response.ok) {
        error.value = response.error ?? '实时操作没有成功'
        return false
      }
      return true
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : '网络连接异常'
      return false
    }
  }

  function publishSpectatorFrame(
    sequence: number,
    state: Record<string, unknown>,
  ): boolean {
    const current = snapshot.value
    if (
      !current
      || current.viewer?.mode === 'spectator'
      || current.phase !== 'playing'
      || !current.spectators?.some(
        spectator => spectator.targetPlayerId === current.self.id,
      )
    ) return false
    socket.emit('arcade:spectator:frame', { sequence, state })
    return true
  }

  async function restartGame() {
    if (rejectSpectatorAction()) return false
    return Boolean(await perform('arcade:restart'))
  }

  async function kickPlayer(playerId: string) {
    if (rejectSpectatorAction()) return false
    return Boolean(await perform('arcade:kick', { target_id: playerId }))
  }

  async function dissolveRoom() {
    if (rejectSpectatorAction()) return false
    return Boolean(await perform('arcade:dissolve'))
  }

  async function sendChat(content: string) {
    if (rejectSpectatorAction()) return false
    return Boolean(await perform('arcade:chat', { content }))
  }

  async function requestGameAction(kind: ArcadeGameRequestKind) {
    if (rejectSpectatorAction()) return false
    return Boolean(await perform('arcade:request', { kind }))
  }

  async function resolveGameRequest(accept: boolean) {
    if (rejectSpectatorAction()) return false
    return Boolean(await perform('arcade:request:resolve', { accept }))
  }

  async function updateRules(options: Record<string, unknown>) {
    if (rejectSpectatorAction()) return false
    return Boolean(await perform('arcade:rules:update', { options }))
  }

  async function returnToRoom() {
    if (snapshot.value) return true
    if (session.value?.mode === 'spectator') return resumeWatch()
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

  function rejectSpectatorAction(): boolean {
    if (!isSpectating.value) return false
    error.value = '观战模式只能查看，不能参与操作'
    return true
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
    realtimeFrame.value = null
    spectatorFrame.value = null
    clearSession()
    error.value = payload.silent ? null : (payload.message ?? fallbackMessage)
  }

  function resetForLogout() {
    snapshot.value = null
    realtimeFrame.value = null
    spectatorFrame.value = null
    connected.value = false
    busy.value = false
    error.value = null
    clearSession()
  }

  return {
    snapshot,
    realtimeFrame,
    spectatorFrame,
    availableRooms,
    connected,
    busy,
    error,
    activeGame,
    activeRoomCode,
    resumableGame,
    resumableRoomCode,
    isSpectating,
    init,
    createRoom,
    joinRoom,
    inspectWatchRoom,
    watchRoom,
    leaveWatch,
    syncActiveRoom,
    detachRoom,
    leaveRoom,
    abandonRoom,
    cleanupRoom,
    startGame,
    action,
    actionWithResult,
    rapidAction,
    realtimeInput,
    publishSpectatorFrame,
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
