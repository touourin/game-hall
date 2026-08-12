<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { History, Settings, Trophy, UsersRound } from '@lucide/vue'
import type { AccountProfile } from '../account'
import type { ArcadeGameKey, GameCatalogItem } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import LeaderboardModal from '../components/LeaderboardModal.vue'
import StatsModal from '../components/StatsModal.vue'
import CleanupRoomButton from '../components/CleanupRoomButton.vue'
import GameHomeHeader from '../components/GameHomeHeader.vue'
import SoloChallengeLauncher from '../components/SoloChallengeLauncher.vue'
import SpectatorBrowser from '../components/SpectatorBrowser.vue'
import MultiplayerMatchLauncher from '../components/MultiplayerMatchLauncher.vue'
import { defaultGameRules } from '../gameRules'
import { isSoloGameKey } from '../gameCatalog'
import AvatarImage from '../components/AvatarImage.vue'

const props = withDefaults(defineProps<{
  game: GameCatalogItem
  account: AccountProfile
  invitedRoom?: string
}>(), { invitedRoom: '' })
const emit = defineEmits<{
  back: []
  settings: []
  roomEntered: [payload: { gameKey: ArcadeGameKey; roomCode: string }]
  resumeRoom: []
}>()
const arcade = useArcadeStore()
const mode = ref<'create' | 'join'>(props.invitedRoom ? 'join' : 'create')
const roomCode = ref(props.invitedRoom.toUpperCase())
const roomName = ref('')
const showStats = ref(false)
const showLeaderboard = ref(false)
const gameKey = computed(() => props.game.key as ArcadeGameKey)
const rules = ref<Record<string, unknown>>(defaultGameRules(gameKey.value))
const isSolo = computed(() => isSoloGameKey(props.game.key))
const statsMode = computed(() => {
  if (gameKey.value === 'minesweeper') return String(rules.value.difficulty)
  if (gameKey.value !== 'tetris') return undefined
  return rules.value.challengeMode === 'endless'
    ? 'standard'
    : `timed_${Number(rules.value.durationSeconds ?? 180)}`
})
const gameRooms = computed(() =>
  arcade.availableRooms.filter((room) => room.gameKey === props.game.key),
)
const rooms = computed(() => gameRooms.value.filter(
  (room) => !room.cleanupAvailable && (room.phase ?? 'lobby') === 'lobby',
))
const watchRooms = computed(() => gameRooms.value.filter(
  (room) => !room.cleanupAvailable && room.watchable,
))
const cleanupRooms = computed(() => gameRooms.value.filter((room) => room.cleanupAvailable))
const canSubmit = computed(
  () => !arcade.activeRoomCode && (
    isSolo.value || mode.value === 'create' || roomCode.value.trim().length >= 4
  ),
)

watch(gameKey, (key) => {
  rules.value = defaultGameRules(key)
})

watch(
  () => props.invitedRoom,
  (invitedRoom) => {
    if (!invitedRoom) return
    mode.value = 'join'
    roomCode.value = invitedRoom.toUpperCase()
  },
)

async function submit() {
  if (!canSubmit.value) return
  const key = props.game.key as ArcadeGameKey
  if (isSolo.value || mode.value === 'create') {
    const normalizedRoomName = roomName.value.trim()
    const created = normalizedRoomName
      ? await arcade.createRoom(key, rules.value, normalizedRoomName)
      : await arcade.createRoom(key, rules.value)
    if (!created) return
    if (isSolo.value) await arcade.startGame()
  }
  else if (!await arcade.joinRoom(key, roomCode.value)) return

  const enteredRoomCode = arcade.activeRoomCode
  if (enteredRoomCode) {
    emit('roomEntered', { gameKey: key, roomCode: enteredRoomCode })
  }
}

</script>

<template>
  <main class="arcade-home page-container adaptive-layout-root" :class="[`game-home-${game.key}`, { 'solo-arcade-home': isSolo }]">
    <GameHomeHeader
      :game-key="game.key"
      :eyebrow="game.players"
      :title="game.name"
      :description="game.description"
      @back="$emit('back')"
    >
      <template #actions>
        <button v-if="!account.isGuest" type="button" @click="showStats = true"><History :size="17" />我的战绩</button>
        <button type="button" @click="showLeaderboard = true"><Trophy :size="17" />排行榜</button>
        <button type="button" aria-label="打开设置" @click="emit('settings')"><Settings :size="17" />设置</button>
      </template>
    </GameHomeHeader>

    <section
      v-if="arcade.activeRoomCode && arcade.activeGame === game.key"
      class="surface resume-arcade-card"
    >
      <div><History :size="20" /><span><strong>你有一局尚未结束</strong><small>房间 {{ arcade.activeRoomCode }}</small></span></div>
      <button type="button" class="primary-button" @click="emit('resumeRoom')">返回对局</button>
    </section>

    <MultiplayerMatchLauncher
      v-if="!isSolo"
      v-model="rules"
      v-model:mode="mode"
      v-model:room-code="roomCode"
      v-model:room-name="roomName"
      :game="game"
      :game-key="gameKey"
      :rooms="rooms"
      :guest="account.isGuest"
      :disabled="!canSubmit"
      :active-room="Boolean(arcade.activeRoomCode)"
      @submit="submit"
    />

    <section v-if="cleanupRooms.length" class="surface cleanup-room-browser">
      <header>
        <div><span class="cleanup-browser-icon"><UsersRound :size="19" /></span><div><strong>待清理的房间</strong><small>所有真人已离线超过 10 分钟</small></div></div>
        <span>{{ cleanupRooms.length }} 间</span>
      </header>
      <div class="cleanup-room-list">
        <article v-for="room in cleanupRooms" :key="room.roomCode" class="cleanup-room-item">
          <AvatarImage class="avatar" :src="room.hostAvatarUrl" :name="room.hostName" />
          <span class="available-room-copy"><strong>{{ room.roomName || `${room.hostName}的房间` }}</strong><small>房间 {{ room.roomCode }} · {{ room.phase === 'lobby' ? '等待阶段' : '未完成对局' }}</small></span>
          <CleanupRoomButton :room-code="room.roomCode" :busy="arcade.busy" @confirm="arcade.cleanupRoom(room.roomCode)" />
        </article>
      </div>
    </section>

    <SoloChallengeLauncher
      v-if="isSolo"
      v-model="rules"
      :game-key="gameKey"
      :disabled="!canSubmit"
      :active-room="Boolean(arcade.activeRoomCode)"
      @start="submit"
    />

    <SpectatorBrowser
      v-if="!['one_night_werewolf', 'tetris'].includes(gameKey)"
      :game-key="gameKey"
      :game-name="game.name"
      :rooms="watchRooms"
      :initial-room-code="invitedRoom"
      :disabled="Boolean(arcade.activeRoomCode)"
      :guest="account.isGuest"
      @watched="emit('roomEntered', $event)"
    />

    <StatsModal
      v-if="showStats && !account.isGuest"
      :game-key="game.key"
      :game-name="game.name"
      :game-mode="statsMode"
      @close="showStats = false"
    />
    <LeaderboardModal
      v-if="showLeaderboard"
      :account-id="account.id"
      :game-key="game.key"
      :game-name="game.name"
      :game-mode="statsMode"
      @close="showLeaderboard = false"
    />
  </main>
</template>

<style scoped>
.arcade-home { width: min(100%, 1120px); padding-bottom: 80px; }
.arcade-home.solo-arcade-home { width: min(100%, 1120px); }
.solo-arcade-home :deep(.game-home-header) { min-height: 178px; padding-bottom: 35px; }
.solo-arcade-home :deep(.game-home-header::after) { bottom: 14px; }
.resume-arcade-card { margin-bottom: 18px; padding: 14px 16px; display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.resume-arcade-card > div { display: flex; align-items: center; gap: 11px; color: var(--gold); }
.resume-arcade-card strong,.resume-arcade-card small { display: block; }.resume-arcade-card small { margin-top: 3px; color: var(--muted); }
.cleanup-room-browser { width: min(100%, 760px); margin: 0 auto; padding: 16px; }
.multiplayer-match-launcher + .cleanup-room-browser { margin-top: 18px; }
.cleanup-room-browser > header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 13px; }
.cleanup-room-browser > header > div { min-width: 0; display: flex; align-items: center; gap: 10px; }
.cleanup-room-browser header strong, .cleanup-room-browser header small { display: block; }.cleanup-room-browser header small { margin-top: 2px; color: var(--muted); }
.cleanup-room-browser > header > span { flex: 0 0 auto; border-radius: 999px; padding: 5px 8px; color: #efaaa7; background: rgba(134, 45, 49, .1); font-size: 11px; font-weight: 800; }
.cleanup-browser-icon { width: 38px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 11px; color: #efaaa7; background: rgba(134, 45, 49, .15); }
.cleanup-room-list { display: grid; gap: 8px; }
.cleanup-room-item { min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 11px; border: 1px solid rgba(231, 119, 119, .24); border-radius: 13px; padding: 11px 12px; background: rgba(96, 32, 36, .1); }
@media (max-width: 600px) {
  .arcade-home { padding-right: 12px; padding-left: 12px; }
  .cleanup-room-browser { padding: 14px; }
  .cleanup-room-browser > header { align-items: flex-start; gap: 8px; }
  .cleanup-room-browser header small { font-size: 10px; line-height: 1.45; }
  .cleanup-room-item { grid-template-columns: auto minmax(0, 1fr); }.cleanup-room-item :deep(.cleanup-room-button) { grid-column: 1 / -1; width: 100%; }
  .resume-arcade-card { align-items: stretch; flex-direction: column; }
  .solo-arcade-home :deep(.game-home-header) { padding-bottom: 27px; }
}
</style>
