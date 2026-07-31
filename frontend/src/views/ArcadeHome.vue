<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { ArrowLeft, ChevronRight, History, LogIn, Plus, Trophy, UsersRound } from '@lucide/vue'
import type { AccountProfile } from '../account'
import type { ArcadeGameKey, GameCatalogItem } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import LeaderboardModal from '../components/LeaderboardModal.vue'
import StatsModal from '../components/StatsModal.vue'

const props = defineProps<{ game: GameCatalogItem; account: AccountProfile }>()
defineEmits<{ back: [] }>()
const arcade = useArcadeStore()
const params = new URLSearchParams(window.location.search)
const invitedRoom = params.get('game') === props.game.key ? params.get('room') ?? '' : ''
const mode = ref<'create' | 'join'>(invitedRoom ? 'join' : 'create')
const roomCode = ref(invitedRoom.toUpperCase())
const name = ref(localStorage.getItem('gamehall:last-name') ?? props.account.displayName)
const joinCard = ref<HTMLElement | null>(null)
const showStats = ref(false)
const showLeaderboard = ref(false)
const rooms = computed(() =>
  arcade.availableRooms.filter((room) => room.gameKey === props.game.key),
)
const canSubmit = computed(
  () => name.value.trim() && (mode.value === 'create' || roomCode.value.trim().length >= 4),
)

async function submit() {
  if (!canSubmit.value) return
  localStorage.setItem('gamehall:last-name', name.value.trim())
  const key = props.game.key as ArcadeGameKey
  if (mode.value === 'create') await arcade.createRoom(key, name.value.trim())
  else await arcade.joinRoom(key, roomCode.value, name.value.trim())
}

async function chooseRoom(code: string) {
  mode.value = 'join'
  roomCode.value = code
  await nextTick()
  joinCard.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<template>
  <main class="arcade-home page-container">
    <header class="game-home-header">
      <button type="button" class="icon-button" aria-label="返回游戏大厅" @click="$emit('back')"><ArrowLeft :size="21" /></button>
      <div><small>{{ game.players }}</small><h1>{{ game.name }}</h1><p>{{ game.description }}</p></div>
      <div class="game-home-actions">
        <button type="button" @click="showStats = true"><History :size="17" />我的战绩</button>
        <button type="button" @click="showLeaderboard = true"><Trophy :size="17" />排行榜</button>
      </div>
    </header>

    <section class="surface room-browser">
      <header>
        <div><span class="room-browser-icon"><UsersRound :size="19" /></span><div><strong>等待中的房间</strong><small>选择后可直接加入</small></div></div>
        <span>{{ rooms.length }} 间</span>
      </header>
      <div v-if="rooms.length" class="available-room-list">
        <button v-for="room in rooms" :key="room.roomCode" type="button" class="available-room" @click="chooseRoom(room.roomCode)">
          <span class="avatar">{{ room.hostName.slice(0, 1) }}</span>
          <span class="available-room-copy"><strong>{{ room.hostName }} 的房间</strong><small>房间 {{ room.roomCode }} · {{ room.playerCount }}/{{ room.maxPlayers }} 人</small></span>
          <ChevronRight :size="18" />
        </button>
      </div>
      <div v-else class="empty-room-list">暂无公开房间，创建第一局吧</div>
    </section>

    <section ref="joinCard" class="surface join-card">
      <div class="segmented-control">
        <button type="button" :class="{ active: mode === 'create' }" @click="mode = 'create'">创建房间</button>
        <button type="button" :class="{ active: mode === 'join' }" @click="mode = 'join'">加入房间</button>
      </div>
      <form @submit.prevent="submit">
        <label class="field"><span>你的称呼</span><input v-model="name" maxlength="12" autocomplete="nickname" /></label>
        <label v-if="mode === 'join'" class="field"><span>房间代码</span><input v-model="roomCode" maxlength="8" class="room-code-input" @input="roomCode = roomCode.toUpperCase()" /></label>
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
      @close="showStats = false"
    />
    <LeaderboardModal
      v-if="showLeaderboard"
      :account-id="account.id"
      :game-key="game.key"
      :game-name="game.name"
      @close="showLeaderboard = false"
    />
  </main>
</template>

<style scoped>
.arcade-home { padding-bottom: 70px; }
.game-home-header { padding: 25px 0 38px; display: grid; grid-template-columns: auto 1fr auto; gap: 18px; align-items: flex-start; }
.game-home-header small { color: var(--gold); font-weight: 800; }.game-home-header h1 { margin: 4px 0; font-family: serif; font-size: clamp(34px, 6vw, 58px); }.game-home-header p { margin: 0; color: var(--muted); }
.game-home-actions { display: flex; gap: 7px; }
.game-home-actions button { display: inline-flex; align-items: center; gap: 6px; padding: 9px 11px; border: 1px solid var(--line); border-radius: 11px; color: var(--muted); background: var(--surface); font-weight: 800; }
.arcade-home .room-browser { margin-bottom: 22px; }
@media (max-width: 600px) {
  .game-home-header { grid-template-columns: auto 1fr; }
  .game-home-actions { grid-column: 1 / -1; justify-content: flex-end; }
}
</style>
