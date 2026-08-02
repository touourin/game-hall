<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { ChevronRight, History, LogIn, Plus, Settings, Trophy, UsersRound } from '@lucide/vue'
import type { AccountProfile } from '../account'
import type { ArcadeGameKey, GameCatalogItem } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import LeaderboardModal from '../components/LeaderboardModal.vue'
import StatsModal from '../components/StatsModal.vue'
import GameRuleSettings from '../components/GameRuleSettings.vue'
import CleanupRoomButton from '../components/CleanupRoomButton.vue'
import GameHomeHeader from '../components/GameHomeHeader.vue'
import SoloChallengeLauncher from '../components/SoloChallengeLauncher.vue'
import { defaultGameRules, gameRuleSummary } from '../gameRules'
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
const joinCard = ref<HTMLElement | null>(null)
const showStats = ref(false)
const showLeaderboard = ref(false)
const gameKey = computed(() => props.game.key as ArcadeGameKey)
const rules = ref<Record<string, unknown>>(defaultGameRules(gameKey.value))
const isSolo = computed(() => ['reaction', 'schulte', 'minesweeper', 'hanoi'].includes(props.game.key))
const gameRooms = computed(() =>
  arcade.availableRooms.filter((room) => room.gameKey === props.game.key),
)
const rooms = computed(() => gameRooms.value.filter((room) => !room.cleanupAvailable))
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
    const created = await arcade.createRoom(key, rules.value)
    if (!created) return
    if (isSolo.value) await arcade.startGame()
  }
  else if (!await arcade.joinRoom(key, roomCode.value)) return

  const enteredRoomCode = arcade.activeRoomCode
  if (enteredRoomCode) {
    emit('roomEntered', { gameKey: key, roomCode: enteredRoomCode })
  }
}

async function chooseRoom(code: string) {
  mode.value = 'join'
  roomCode.value = code
  await nextTick()
  joinCard.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<template>
  <main class="arcade-home page-container" :class="[`game-home-${game.key}`, { 'solo-arcade-home': isSolo }]">
    <GameHomeHeader
      :eyebrow="game.players"
      :title="game.name"
      :description="game.description"
      @back="$emit('back')"
    >
      <template #actions>
        <button type="button" @click="showStats = true"><History :size="17" />我的战绩</button>
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

    <section v-if="!isSolo" class="surface room-browser">
      <header>
        <div><span class="room-browser-icon"><UsersRound :size="19" /></span><div><strong>等待中的房间</strong><small>选择后可直接加入</small></div></div>
        <span>{{ rooms.length }} 间</span>
      </header>
      <div v-if="rooms.length" class="available-room-list">
        <button v-for="room in rooms" :key="room.roomCode" type="button" class="available-room" @click="chooseRoom(room.roomCode)">
          <AvatarImage class="avatar" :src="room.hostAvatarUrl" :name="room.hostName" />
          <span class="available-room-copy"><strong>{{ room.hostName }} 的房间</strong><small>房间 {{ room.roomCode }} · {{ room.playerCount }}/{{ room.maxPlayers }} 人<br>{{ gameRuleSummary(room.gameKey, room.options) }}</small></span>
          <ChevronRight :size="18" />
        </button>
      </div>
      <div v-else class="empty-room-list">暂无公开房间，创建第一局吧</div>
    </section>

    <section v-if="cleanupRooms.length" class="surface cleanup-room-browser">
      <header>
        <div><span class="cleanup-browser-icon"><UsersRound :size="19" /></span><div><strong>待清理的房间</strong><small>所有真人已离线超过 10 分钟</small></div></div>
        <span>{{ cleanupRooms.length }} 间</span>
      </header>
      <div class="cleanup-room-list">
        <article v-for="room in cleanupRooms" :key="room.roomCode" class="cleanup-room-item">
          <AvatarImage class="avatar" :src="room.hostAvatarUrl" :name="room.hostName" />
          <span class="available-room-copy"><strong>{{ room.hostName }} 的房间</strong><small>房间 {{ room.roomCode }} · {{ room.phase === 'lobby' ? '等待阶段' : '未完成对局' }}</small></span>
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

    <section v-else ref="joinCard" class="surface join-card">
      <div class="segmented-control">
        <button type="button" :class="{ active: mode === 'create' }" @click="mode = 'create'">创建房间</button>
        <button type="button" :class="{ active: mode === 'join' }" @click="mode = 'join'">加入房间</button>
      </div>
      <form @submit.prevent="submit">
        <GameRuleSettings
          v-if="mode === 'create'"
          v-model="rules"
          :game-key="gameKey"
          class="create-rule-settings"
        />
        <label v-if="mode === 'join'" class="field"><span>房间代码</span><input v-model="roomCode" maxlength="8" class="room-code-input" @input="roomCode = roomCode.toUpperCase()" /></label>
        <p v-if="arcade.activeRoomCode" class="active-room-hint">请先返回并退出当前房间，再开始或加入其他对局。</p>
        <button type="submit" class="primary-button wide-button" :disabled="!canSubmit">
          <Plus v-if="mode === 'create'" :size="19" /><LogIn v-else :size="19" />
          {{ mode === 'create' ? `创建${game.name}房间` : '进入房间' }}
        </button>
      </form>
    </section>

    <StatsModal
      v-if="showStats"
      :game-key="game.key"
      :game-name="game.name"
      :game-mode="game.key === 'minesweeper' ? String(rules.difficulty) : undefined"
      @close="showStats = false"
    />
    <LeaderboardModal
      v-if="showLeaderboard"
      :account-id="account.id"
      :game-key="game.key"
      :game-name="game.name"
      :game-mode="game.key === 'minesweeper' ? String(rules.difficulty) : undefined"
      @close="showLeaderboard = false"
    />
  </main>
</template>

<style scoped>
.arcade-home { width: min(100%, 980px); padding-bottom: 80px; }
.arcade-home.solo-arcade-home { width: min(100%, 1120px); }
.solo-arcade-home :deep(.game-home-header) { min-height: 178px; padding-bottom: 35px; }
.solo-arcade-home :deep(.game-home-header::after) { bottom: 14px; }
.resume-arcade-card { margin-bottom: 18px; padding: 14px 16px; display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.resume-arcade-card > div { display: flex; align-items: center; gap: 11px; color: var(--gold); }
.resume-arcade-card strong,.resume-arcade-card small { display: block; }.resume-arcade-card small { margin-top: 3px; color: var(--muted); }
.arcade-home .room-browser { margin-bottom: 18px; }
.arcade-home .join-card { width: min(100%, 760px); margin: 28px auto 0; padding: 10px 26px 26px; }
.cleanup-room-browser { width: min(100%, 760px); margin: 0 auto; padding: 16px; }
.cleanup-room-browser + .join-card { margin-top: 18px; }
.cleanup-room-browser > header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 13px; }
.cleanup-room-browser > header > div { min-width: 0; display: flex; align-items: center; gap: 10px; }
.cleanup-room-browser header strong, .cleanup-room-browser header small { display: block; }.cleanup-room-browser header small { margin-top: 2px; color: var(--muted); }
.cleanup-room-browser > header > span { flex: 0 0 auto; border-radius: 999px; padding: 5px 8px; color: #efaaa7; background: rgba(134, 45, 49, .1); font-size: 11px; font-weight: 800; }
.cleanup-browser-icon { width: 38px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 11px; color: #efaaa7; background: rgba(134, 45, 49, .15); }
.cleanup-room-list { display: grid; gap: 8px; }
.cleanup-room-item { min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 11px; border: 1px solid rgba(231, 119, 119, .24); border-radius: 13px; padding: 11px 12px; background: rgba(96, 32, 36, .1); }
.create-rule-settings { margin-bottom: 22px; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 21px 2px; }
.active-room-hint { margin: 0 0 12px; color: var(--muted); font-size: 12px; text-align: center; }
@media (max-width: 600px) {
  .arcade-home { padding-right: 12px; padding-left: 12px; }
  .arcade-home .join-card { margin-top: 18px; padding: 8px 14px 16px; }
  .create-rule-settings { margin-bottom: 16px; padding: 16px 0; }
  .cleanup-room-browser { padding: 14px; }
  .cleanup-room-browser > header { align-items: flex-start; gap: 8px; }
  .cleanup-room-browser header small { font-size: 10px; line-height: 1.45; }
  .cleanup-room-item { grid-template-columns: auto minmax(0, 1fr); }.cleanup-room-item :deep(.cleanup-room-button) { grid-column: 1 / -1; width: 100%; }
  .resume-arcade-card { align-items: stretch; flex-direction: column; }
  .solo-arcade-home :deep(.game-home-header) { padding-bottom: 27px; }
}
</style>
