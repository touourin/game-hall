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
const junqiMode = ref<'dark' | 'flip'>('dark')
const isSolo = computed(() => props.game.key === 'reaction')
const rooms = computed(() =>
  arcade.availableRooms.filter((room) => room.gameKey === props.game.key),
)
const canSubmit = computed(
  () => name.value.trim() && (isSolo.value || mode.value === 'create' || roomCode.value.trim().length >= 4),
)

async function submit() {
  if (!canSubmit.value) return
  localStorage.setItem('gamehall:last-name', name.value.trim())
  const key = props.game.key as ArcadeGameKey
  if (isSolo.value || mode.value === 'create') {
    const options = key === 'junqi' ? { mode: junqiMode.value } : {}
    const created = await arcade.createRoom(key, name.value.trim(), options)
    if (created && isSolo.value) await arcade.startGame()
  }
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

    <section v-if="!isSolo" class="surface room-browser">
      <header>
        <div><span class="room-browser-icon"><UsersRound :size="19" /></span><div><strong>等待中的房间</strong><small>选择后可直接加入</small></div></div>
        <span>{{ rooms.length }} 间</span>
      </header>
      <div v-if="rooms.length" class="available-room-list">
        <button v-for="room in rooms" :key="room.roomCode" type="button" class="available-room" @click="chooseRoom(room.roomCode)">
          <span class="avatar">{{ room.hostName.slice(0, 1) }}</span>
          <span class="available-room-copy"><strong>{{ room.hostName }} 的房间</strong><small>房间 {{ room.roomCode }} · {{ room.playerCount }}/{{ room.maxPlayers }} 人<span v-if="game.key === 'junqi'"> · {{ room.options.mode === 'flip' ? '翻棋军旗' : '暗军旗' }}</span></small></span>
          <ChevronRight :size="18" />
        </button>
      </div>
      <div v-else class="empty-room-list">暂无公开房间，创建第一局吧</div>
    </section>

    <section ref="joinCard" class="surface join-card">
      <div v-if="!isSolo" class="segmented-control">
        <button type="button" :class="{ active: mode === 'create' }" @click="mode = 'create'">创建房间</button>
        <button type="button" :class="{ active: mode === 'join' }" @click="mode = 'join'">加入房间</button>
      </div>
      <div v-else class="solo-game-intro">
        <span class="solo-game-mark">⚡</span>
        <div>
          <strong>准备测试你的反应速度</strong>
          <small>共三轮；看到按钮变绿后，按空格键或直接点击</small>
        </div>
      </div>
      <form @submit.prevent="submit">
        <label v-if="!isSolo" class="field"><span>你的称呼</span><input v-model="name" maxlength="12" autocomplete="nickname" /></label>
        <fieldset v-if="game.key === 'junqi' && mode === 'create'" class="junqi-mode-picker">
          <legend>选择军旗玩法</legend>
          <button type="button" :class="{ active: junqiMode === 'dark' }" @click="junqiMode = 'dark'">
            <strong>暗军旗</strong><small>各自秘密布阵，再轮流行棋</small>
          </button>
          <button type="button" :class="{ active: junqiMode === 'flip' }" @click="junqiMode = 'flip'">
            <strong>翻棋军旗</strong><small>随机扣棋，首翻决定阵营</small>
          </button>
        </fieldset>
        <label v-if="!isSolo && mode === 'join'" class="field"><span>房间代码</span><input v-model="roomCode" maxlength="8" class="room-code-input" @input="roomCode = roomCode.toUpperCase()" /></label>
        <button type="submit" class="primary-button wide-button" :disabled="!canSubmit">
          <Plus v-if="isSolo || mode === 'create'" :size="19" /><LogIn v-else :size="19" />
          {{ isSolo ? '开始三轮反应测试' : mode === 'create' ? `创建${game.name}房间` : '进入房间' }}
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
.junqi-mode-picker { width: 100%; min-width: 0; margin: 0 0 16px; padding: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; border: 0; }
.junqi-mode-picker legend { margin-bottom: 8px; color: var(--muted); font-size: 13px; font-weight: 800; }
.junqi-mode-picker button { min-height: 78px; padding: 14px; display: grid; align-content: center; gap: 4px; text-align: left; border: 1px solid var(--line); border-radius: 13px; color: var(--text); background: var(--surface); }
.junqi-mode-picker button.active { border-color: var(--gold); background: #d6ae5114; box-shadow: inset 0 0 0 1px #d6ae5138; }
.junqi-mode-picker small { color: var(--muted); line-height: 1.4; }
.solo-game-intro { margin: 4px 0 20px; padding: 14px 4px 4px; display: flex; align-items: center; gap: 12px; }
.solo-game-mark { width: 46px; aspect-ratio: 1; display: grid; flex: 0 0 auto; place-items: center; border: 1px solid #78d2aa55; border-radius: 14px; color: #8fe0bd; background: #62c69b16; font-size: 22px; }
.solo-game-intro strong, .solo-game-intro small { display: block; }.solo-game-intro small { margin-top: 4px; color: var(--muted); line-height: 1.5; }
@media (max-width: 600px) {
  .game-home-header { padding: 18px 0 26px; grid-template-columns: auto minmax(0, 1fr); gap: 14px; }
  .game-home-actions { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); width: 100%; }
  .game-home-actions button { min-height: 42px; justify-content: center; }
  .junqi-mode-picker { grid-template-columns: 1fr; }
}
</style>
