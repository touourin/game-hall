<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { History, RotateCcw, Settings, Trophy, UsersRound } from '@lucide/vue'
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
import { gameRegistration } from '../game-platform/registry'
import AvatarImage from '../components/AvatarImage.vue'
import UiButton from '../components/ui/UiButton.vue'

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
const registration = computed(() => gameRegistration(gameKey.value))
const statsMode = computed(
  () => registration.value?.records?.modeFromRules?.(rules.value),
)
const canSpectate = computed(
  () => registration.value?.capabilities.spectators ?? true,
)
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
        <button v-if="!account.isGuest" type="button" data-ui-interaction="choice" @click="showStats = true"><History :size="17" />我的战绩</button>
        <button type="button" data-ui-interaction="choice" @click="showLeaderboard = true"><Trophy :size="17" />排行榜</button>
        <button type="button" data-ui-interaction="choice" aria-label="打开设置" @click="emit('settings')"><Settings :size="17" />设置</button>
      </template>
    </GameHomeHeader>

    <section
      v-if="arcade.activeRoomCode && arcade.activeGame === game.key"
      class="surface resume-arcade-card"
      aria-label="进行中的对局"
    >
      <div class="resume-arcade-copy">
        <span class="resume-arcade-icon"><RotateCcw :size="19" /></span>
        <span>
          <small>对局进行中</small>
          <strong>{{ game.name }}</strong>
          <em>房间 {{ arcade.activeRoomCode }}</em>
        </span>
      </div>
      <UiButton variant="primary" @click="emit('resumeRoom')">返回对局</UiButton>
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
      v-if="canSpectate"
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
.resume-arcade-card { margin-bottom: 18px; padding: 11px 12px; display: flex; align-items: center; justify-content: space-between; gap: 14px; border-color: color-mix(in srgb, var(--accent) 28%, var(--line)); }
.resume-arcade-copy { display: flex; min-width: 0; align-items: center; gap: 10px; }
.resume-arcade-icon { display: grid; place-items: center; width: 38px; aspect-ratio: 1; flex: 0 0 auto; border-radius: 11px; color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, var(--surface-soft)); }
.resume-arcade-copy > span:last-child { display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: baseline; min-width: 0; }
.resume-arcade-copy small { grid-column: 1 / -1; margin-bottom: 2px; color: var(--accent); font-size: 9px; font-weight: 800; letter-spacing: .06em; }
.resume-arcade-copy strong,.resume-arcade-copy em { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.resume-arcade-copy strong { font-size: 13px; }
.resume-arcade-copy em { margin-left: 8px; color: var(--muted); font-size: 10px; font-style: normal; }
.resume-arcade-card :deep(.ui-button) { min-height: 40px; }
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
