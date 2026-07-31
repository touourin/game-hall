<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import {
  ChevronRight,
  Crown,
  LogIn,
  Plus,
  ShieldCheck,
  Sparkles,
  UsersRound,
} from '@lucide/vue'
import { useRoomStore } from '../stores/room'

const room = useRoomStore()
const params = new URLSearchParams(window.location.search)
const initialRoomCode = params.get('room')?.toUpperCase() ?? ''
const mode = ref<'create' | 'join'>(initialRoomCode ? 'join' : 'create')
const name = ref(localStorage.getItem('avalon:last-name') ?? '')
const roomCode = ref(initialRoomCode)
const joinCard = ref<HTMLElement | null>(null)

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

    <p class="home-note">无需注册 · 适合 5–10 人 · 请连接同一个 Wi‑Fi</p>
  </main>
</template>
