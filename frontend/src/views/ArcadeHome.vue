<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { ChevronRight, History, LogIn, Plus, Trophy, UsersRound } from '@lucide/vue'
import type { AccountProfile } from '../account'
import type { ArcadeGameKey, GameCatalogItem } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import LeaderboardModal from '../components/LeaderboardModal.vue'
import StatsModal from '../components/StatsModal.vue'
import GameRuleSettings from '../components/GameRuleSettings.vue'
import CleanupRoomButton from '../components/CleanupRoomButton.vue'
import GameHomeHeader from '../components/GameHomeHeader.vue'
import { defaultGameRules, gameRuleSummary } from '../gameRules'
import AvatarImage from '../components/AvatarImage.vue'

const props = defineProps<{ game: GameCatalogItem; account: AccountProfile }>()
defineEmits<{ back: [] }>()
const arcade = useArcadeStore()
const params = new URLSearchParams(window.location.search)
const invitedRoom = params.get('game') === props.game.key ? params.get('room') ?? '' : ''
const mode = ref<'create' | 'join'>(invitedRoom ? 'join' : 'create')
const roomCode = ref(invitedRoom.toUpperCase())
const joinCard = ref<HTMLElement | null>(null)
const showStats = ref(false)
const showLeaderboard = ref(false)
const gameKey = computed(() => props.game.key as ArcadeGameKey)
const rules = ref<Record<string, unknown>>(defaultGameRules(gameKey.value))
const isSolo = computed(() => ['reaction', 'schulte', 'minesweeper', 'hanoi'].includes(props.game.key))
const soloIntro = computed(() => {
  if (props.game.key === 'hanoi') {
    return {
      mark: '塔',
      title: '把整座圆盘移到最右侧',
      description: '每次只能移动最上方一块，大圆盘不能压在小圆盘上',
      button: '开始汉诺塔挑战',
    }
  }
  if (props.game.key === 'schulte') {
    return {
      mark: '格',
      title: '按顺序找到 1–25',
      description: '5×5 标准挑战，服务端计时并验证每一次点击',
      button: '开始舒尔特挑战',
    }
  }
  if (props.game.key === 'minesweeper') {
    return {
      mark: '雷',
      title: '清除所有安全方格',
      description: '首次点击安全；电脑右键、手机长按或插旗模式均可标记地雷',
      button: '开始扫雷挑战',
    }
  }
  return {
      mark: '⚡',
      title: '准备测试你的反应速度',
      description: '共三轮；看到按钮变绿后，按空格键或直接点击',
      button: '开始反应挑战',
    }
})
const gameRooms = computed(() =>
  arcade.availableRooms.filter((room) => room.gameKey === props.game.key),
)
const rooms = computed(() => gameRooms.value.filter((room) => !room.cleanupAvailable))
const cleanupRooms = computed(() => gameRooms.value.filter((room) => room.cleanupAvailable))
const canSubmit = computed(
  () => isSolo.value || mode.value === 'create' || roomCode.value.trim().length >= 4,
)

watch(gameKey, (key) => {
  rules.value = defaultGameRules(key)
})

async function submit() {
  if (!canSubmit.value) return
  const key = props.game.key as ArcadeGameKey
  if (isSolo.value || mode.value === 'create') {
    const created = await arcade.createRoom(key, rules.value)
    if (created && isSolo.value) await arcade.startGame()
  }
  else await arcade.joinRoom(key, roomCode.value)
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
    <GameHomeHeader
      :eyebrow="game.players"
      :title="game.name"
      :description="game.description"
      @back="$emit('back')"
    >
      <template #actions>
        <button type="button" @click="showStats = true"><History :size="17" />我的战绩</button>
        <button type="button" @click="showLeaderboard = true"><Trophy :size="17" />排行榜</button>
      </template>
    </GameHomeHeader>

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

    <section ref="joinCard" class="surface join-card">
      <div v-if="!isSolo" class="segmented-control">
        <button type="button" :class="{ active: mode === 'create' }" @click="mode = 'create'">创建房间</button>
        <button type="button" :class="{ active: mode === 'join' }" @click="mode = 'join'">加入房间</button>
      </div>
      <div v-else class="solo-game-intro">
        <span class="solo-game-mark">{{ soloIntro.mark }}</span>
        <div>
          <strong>{{ soloIntro.title }}</strong>
          <small>{{ soloIntro.description }}</small>
        </div>
      </div>
      <form @submit.prevent="submit">
        <GameRuleSettings
          v-if="mode === 'create' && !['reaction', 'schulte'].includes(gameKey)"
          v-model="rules"
          :game-key="gameKey"
          class="create-rule-settings"
        />
        <label v-if="!isSolo && mode === 'join'" class="field"><span>房间代码</span><input v-model="roomCode" maxlength="8" class="room-code-input" @input="roomCode = roomCode.toUpperCase()" /></label>
        <button type="submit" class="primary-button wide-button" :disabled="!canSubmit">
          <Plus v-if="isSolo || mode === 'create'" :size="19" /><LogIn v-else :size="19" />
          {{ isSolo ? soloIntro.button : mode === 'create' ? `创建${game.name}房间` : '进入房间' }}
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
.arcade-home { padding-bottom: 70px; }
.arcade-home .room-browser { margin-bottom: 22px; }
.cleanup-room-browser { margin-bottom: 22px; }
.cleanup-room-browser > header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 13px; }
.cleanup-room-browser > header > div { display: flex; align-items: center; gap: 10px; }
.cleanup-room-browser header strong, .cleanup-room-browser header small { display: block; }.cleanup-room-browser header small { margin-top: 2px; color: var(--muted); }
.cleanup-browser-icon { width: 38px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 11px; color: #efaaa7; background: rgba(134, 45, 49, .15); }
.cleanup-room-list { display: grid; gap: 8px; }
.cleanup-room-item { min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 11px; border: 1px solid rgba(231, 119, 119, .24); border-radius: 13px; padding: 11px 12px; background: rgba(96, 32, 36, .1); }
.create-rule-settings { margin-bottom: 20px; border: 1px solid var(--line); border-radius: 16px; padding: 16px; background: color-mix(in srgb, var(--surface) 72%, transparent); }
.solo-game-intro { margin: 4px 0 20px; padding: 14px 4px 4px; display: flex; align-items: center; gap: 12px; }
.solo-game-mark { width: 46px; aspect-ratio: 1; display: grid; flex: 0 0 auto; place-items: center; border: 1px solid #78d2aa55; border-radius: 14px; color: #8fe0bd; background: #62c69b16; font-size: 22px; }
.solo-game-intro strong, .solo-game-intro small { display: block; }.solo-game-intro small { margin-top: 4px; color: var(--muted); line-height: 1.5; }
@media (max-width: 600px) {
  .cleanup-room-item { grid-template-columns: auto minmax(0, 1fr); }.cleanup-room-item :deep(.cleanup-room-button) { grid-column: 1 / -1; width: 100%; }
}
</style>
