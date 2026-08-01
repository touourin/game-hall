<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import {
  ChevronRight,
  ArrowLeft,
  Crown,
  History,
  LogIn,
  LogOut,
  Palette,
  Plus,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Trophy,
  UsersRound,
} from '@lucide/vue'
import { useRoomStore } from '../games/avalon/store'
import type { AccountProfile } from '../account'
import LeaderboardModal from '../components/LeaderboardModal.vue'
import StatsModal from '../components/StatsModal.vue'
import ThemeModal from '../components/ThemeModal.vue'

const props = defineProps<{ account: AccountProfile }>()
defineEmits<{ logout: []; back: [] }>()

const room = useRoomStore()
const params = new URLSearchParams(window.location.search)
const initialRoomCode = params.get('room')?.toUpperCase() ?? ''
const mode = ref<'create' | 'join'>(initialRoomCode ? 'join' : 'create')
const name = ref(
  localStorage.getItem('avalon:last-name') ?? props.account.displayName,
)
const roomCode = ref(initialRoomCode)
const joinCard = ref<HTMLElement | null>(null)
const showStats = ref(false)
const showLeaderboard = ref(false)
const showTheme = ref(false)

const canSubmit = computed(
  () =>
    name.value.trim().length > 0 &&
    (mode.value === 'create' || roomCode.value.trim().length >= 4),
)

async function submit() {
  if (!canSubmit.value) return
  localStorage.setItem('avalon:last-name', name.value.trim())
  if (mode.value === 'create') {
    await room.createRoom(name.value.trim())
  } else {
    await room.joinRoom(roomCode.value, name.value.trim())
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
    <section class="account-bar" aria-label="当前登录账号">
      <div>
        <span class="avatar">{{ account.displayName.slice(0, 1) }}</span>
        <span>
          <small>已登录</small>
          <strong>{{ account.displayName }}</strong>
        </span>
      </div>
      <div class="account-bar-actions">
        <button type="button" aria-label="返回游戏大厅" @click="$emit('back')">
          <ArrowLeft :size="16" /><span>大厅</span>
        </button>
        <button type="button" aria-label="查看战绩" @click="showStats = true">
          <History :size="16" /><span>战绩</span>
        </button>
        <button type="button" aria-label="查看排行榜" @click="showLeaderboard = true">
          <Trophy :size="16" /><span>排行榜</span>
        </button>
        <button type="button" aria-label="选择界面主题" @click="showTheme = true">
          <Palette :size="16" /><span>主题</span>
        </button>
        <button type="button" aria-label="退出账号" @click="$emit('logout')">
          <LogOut :size="16" /><span>退出</span>
        </button>
      </div>
    </section>

    <section class="brand-hero">
      <div class="brand-mark" aria-hidden="true">
        <Crown :size="34" />
      </div>
      <p class="eyebrow">AVALON · LAN EDITION</p>
      <h1>圆桌密令</h1>
      <p class="hero-copy">同一局域网，拿起手机就能开始一场忠诚与谎言的较量。</p>
      <div class="feature-row">
        <span><ShieldCheck :size="15" /> 身份私密</span>
        <span><Sparkles :size="15" /> 湖中仙女</span>
      </div>
    </section>

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
        <span>{{ room.availableRooms.length }} 间</span>
      </header>

      <div v-if="room.availableRooms.length" class="available-room-list">
        <button
          v-for="availableRoom in room.availableRooms"
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
        <label class="field">
          <span>你的称呼</span>
          <input
            v-model="name"
            maxlength="12"
            autocomplete="nickname"
            placeholder="例如：兰斯洛特"
          />
        </label>

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
    <ThemeModal v-if="showTheme" @close="showTheme = false" />
  </main>
</template>

<style scoped>
@media (max-width: 680px) {
  .home-page {
    align-content: start;
    gap: 20px;
  }

  .account-bar {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 10px;
    padding: 0 0 12px;
  }

  .account-bar > div:first-child {
    min-width: 0;
  }

  .account-bar > div:first-child strong {
    max-width: min(68vw, 260px);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .account-bar .account-bar-actions {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    width: 100%;
    gap: 6px;
  }

  .account-bar button {
    width: 100%;
    min-width: 0;
    min-height: 46px;
    padding: 5px 2px;
    flex-direction: column;
    justify-content: center;
    gap: 2px;
  }

  .account-bar button span {
    display: block;
    line-height: 1;
    white-space: nowrap;
  }

  .brand-hero {
    padding-top: 4px;
  }

  .brand-mark {
    width: 58px;
    height: 58px;
    margin-bottom: 14px;
  }

  .brand-hero h1 {
    font-size: clamp(40px, 13vw, 56px);
  }
}
</style>
