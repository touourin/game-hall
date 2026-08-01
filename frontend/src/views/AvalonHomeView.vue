<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import {
  ChevronRight,
  History,
  LogIn,
  Plus,
  RotateCcw,
  Trophy,
  UsersRound,
} from '@lucide/vue'
import { useRoomStore } from '../games/avalon/store'
import type { AccountProfile } from '../account'
import LeaderboardModal from '../components/LeaderboardModal.vue'
import StatsModal from '../components/StatsModal.vue'
import CleanupRoomButton from '../components/CleanupRoomButton.vue'
import GameHomeHeader from '../components/GameHomeHeader.vue'

defineProps<{ account: AccountProfile }>()
defineEmits<{ back: [] }>()

const room = useRoomStore()
const params = new URLSearchParams(window.location.search)
const initialRoomCode = params.get('room')?.toUpperCase() ?? ''
const mode = ref<'create' | 'join'>(initialRoomCode ? 'join' : 'create')
const roomCode = ref(initialRoomCode)
const joinCard = ref<HTMLElement | null>(null)
const showStats = ref(false)
const showLeaderboard = ref(false)
const joinableRooms = computed(() =>
  room.availableRooms.filter((availableRoom) => !availableRoom.cleanupAvailable),
)
const cleanupRooms = computed(() =>
  room.availableRooms.filter((availableRoom) => availableRoom.cleanupAvailable),
)

const canSubmit = computed(
  () => mode.value === 'create' || roomCode.value.trim().length >= 4,
)

async function submit() {
  if (!canSubmit.value) return
  if (mode.value === 'create') {
    await room.createRoom()
  } else {
    await room.joinRoom(roomCode.value)
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
  <main class="home-page page-container">
    <GameHomeHeader
      eyebrow="5–10 人"
      title="阿瓦隆"
      description="身份推理、组队投票与湖中仙女"
      @back="$emit('back')"
    >
      <template #actions>
        <button type="button" @click="showStats = true"><History :size="17" />我的战绩</button>
        <button type="button" @click="showLeaderboard = true"><Trophy :size="17" />排行榜</button>
      </template>
    </GameHomeHeader>

    <section
      v-if="room.resumableRoomCode"
      class="surface resume-room-card"
    >
      <div>
        <span class="resume-room-icon"><RotateCcw :size="20" /></span>
        <div>
          <strong>你有一局正在进行</strong>
          <small>房间 {{ room.resumableRoomCode }} · 座位和身份仍为你保留</small>
        </div>
      </div>
      <button
        class="primary-button"
        type="button"
        :disabled="room.busy"
        @click="room.returnToRoom"
      >
        返回游戏 <ChevronRight :size="17" />
      </button>
    </section>

    <section class="surface room-browser">
      <header>
        <div>
          <span class="room-browser-icon"><UsersRound :size="19" /></span>
          <div>
            <strong>正在等待的圆桌</strong>
            <small>选择房间即可带入房间号</small>
          </div>
        </div>
        <span>{{ joinableRooms.length }} 间</span>
      </header>

      <div v-if="joinableRooms.length" class="available-room-list">
        <button
          v-for="availableRoom in joinableRooms"
          :key="availableRoom.roomCode"
          type="button"
          class="available-room"
          @click="chooseRoom(availableRoom.roomCode)"
        >
          <span class="avatar">{{ availableRoom.hostName.slice(0, 1) }}</span>
          <span class="available-room-copy">
            <strong>{{ availableRoom.hostName }} 的圆桌</strong>
            <small>
              房间 {{ availableRoom.roomCode }} ·
              {{ availableRoom.playerCount }}/{{ availableRoom.maxPlayers }} 人
            </small>
          </span>
          <span v-if="availableRoom.ladyEnabled" class="room-feature">湖中仙女</span>
          <ChevronRight :size="18" />
        </button>
      </div>
      <div v-else class="empty-room-list">
        暂无公开房间，创建一个新的圆桌吧
      </div>
    </section>

    <section v-if="cleanupRooms.length" class="surface cleanup-room-browser">
      <header>
        <div>
          <span class="cleanup-browser-icon"><UsersRound :size="19" /></span>
          <div><strong>待清理的圆桌</strong><small>所有真人已离线超过 10 分钟</small></div>
        </div>
        <span>{{ cleanupRooms.length }} 间</span>
      </header>
      <div class="cleanup-room-list">
        <article v-for="availableRoom in cleanupRooms" :key="availableRoom.roomCode" class="cleanup-room-item">
          <span class="avatar">{{ availableRoom.hostName.slice(0, 1) }}</span>
          <span class="available-room-copy">
            <strong>{{ availableRoom.hostName }} 的圆桌</strong>
            <small>房间 {{ availableRoom.roomCode }} · {{ availableRoom.phase === 'lobby' ? '等待阶段' : '未完成对局' }}</small>
          </span>
          <CleanupRoomButton
            :room-code="availableRoom.roomCode"
            :busy="room.busy"
            @confirm="room.cleanupRoom(availableRoom.roomCode)"
          />
        </article>
      </div>
    </section>

    <section ref="joinCard" class="surface join-card">
      <div class="segmented-control" aria-label="选择加入方式">
        <button
          :class="{ active: mode === 'create' }"
          type="button"
          @click="mode = 'create'"
        >
          创建房间
        </button>
        <button
          :class="{ active: mode === 'join' }"
          type="button"
          @click="mode = 'join'"
        >
          加入房间
        </button>
      </div>

      <form @submit.prevent="submit">
        <label v-if="mode === 'join'" class="field">
          <span>房间代码</span>
          <input
            v-model="roomCode"
            class="room-code-input"
            maxlength="8"
            autocapitalize="characters"
            autocomplete="off"
            placeholder="输入四位代码"
            @input="roomCode = roomCode.toUpperCase()"
          />
        </label>

        <button class="primary-button wide-button" type="submit" :disabled="!canSubmit">
          <Plus v-if="mode === 'create'" :size="19" />
          <LogIn v-else :size="19" />
          {{ mode === 'create' ? '建立圆桌' : '进入圆桌' }}
        </button>
      </form>
    </section>

    <p class="home-note">战绩绑定账号 · 适合 5–10 人 · 请连接同一个 Wi‑Fi</p>

    <StatsModal v-if="showStats" game-key="avalon" game-name="阿瓦隆" @close="showStats = false" />
    <LeaderboardModal
      v-if="showLeaderboard"
      :account-id="account.id"
      game-key="avalon"
      game-name="阿瓦隆"
      @close="showLeaderboard = false"
    />
  </main>
</template>

<style scoped>
.cleanup-room-browser { margin-bottom: 22px; overflow: hidden; }
.cleanup-room-browser > header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 13px; }
.cleanup-room-browser > header > div { display: flex; align-items: center; gap: 10px; }
.cleanup-room-browser header strong, .cleanup-room-browser header small { display: block; }
.cleanup-room-browser header small { margin-top: 2px; color: var(--muted); }
.cleanup-browser-icon { width: 38px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 11px; color: #efaaa7; background: rgba(134, 45, 49, .15); }
.cleanup-room-list { display: grid; gap: 8px; }
.cleanup-room-item { min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 11px; border: 1px solid rgba(231, 119, 119, .24); border-radius: 13px; padding: 11px 12px; background: rgba(96, 32, 36, .1); }
@media (max-width: 680px) {
  .cleanup-room-item { grid-template-columns: auto minmax(0, 1fr); }
  .cleanup-room-item :deep(.cleanup-room-button) { grid-column: 1 / -1; width: 100%; }
  .home-page {
    align-content: start;
    gap: 20px;
  }

}
</style>
