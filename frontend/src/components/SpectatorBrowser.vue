<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Eye, Radio, Search, UsersRound } from '@lucide/vue'
import type { ArcadeGameKey, ArcadeLobbyRoom } from '../types/arcade'
import { useArcadeStore } from '../stores/arcade'
import AvatarImage from './AvatarImage.vue'

const props = withDefaults(defineProps<{
  gameKey: ArcadeGameKey
  gameName: string
  rooms: ArcadeLobbyRoom[]
  initialRoomCode?: string
  disabled?: boolean
  guest?: boolean
}>(), {
  initialRoomCode: '',
  disabled: false,
  guest: false,
})

const emit = defineEmits<{
  watched: [payload: { gameKey: ArcadeGameKey; roomCode: string }]
}>()

const arcade = useArcadeStore()
const roomCode = ref(props.initialRoomCode.toUpperCase())
const selectedRoom = ref<ArcadeLobbyRoom | null>(null)
const targets = computed(() => selectedRoom.value?.players ?? [])

watch(
  () => props.initialRoomCode,
  (value) => {
    if (value) roomCode.value = value.toUpperCase()
  },
)

function selectRoom(room: ArcadeLobbyRoom) {
  selectedRoom.value = room
  roomCode.value = room.roomCode
}

async function inspectRoom() {
  const normalized = roomCode.value.trim().toUpperCase()
  if (normalized.length < 4 || props.disabled) return
  const listed = props.rooms.find((room) => room.roomCode === normalized)
  selectedRoom.value = listed
    ?? await arcade.inspectWatchRoom(props.gameKey, normalized)
}

async function watchPlayer(playerId: string) {
  const room = selectedRoom.value
  if (!room || props.disabled) return
  if (await arcade.watchRoom(props.gameKey, room.roomCode, playerId)) {
    emit('watched', { gameKey: props.gameKey, roomCode: room.roomCode })
  }
}
</script>

<template>
  <section class="spectator-browser surface" aria-label="第一人称观战">
    <header>
      <span class="spectator-browser-icon"><Eye :size="20" /></span>
      <span><strong>第一人称观战</strong><small>选择一名玩家，固定观看他能看到的画面</small></span>
      <b><Radio :size="12" />{{ rooms.length }} 局进行中</b>
    </header>

    <div v-if="rooms.length" class="spectator-room-list">
      <button
        v-for="room in rooms"
        :key="room.roomCode"
        type="button"
        data-ui-interaction="choice"
        :class="{ selected: selectedRoom?.roomCode === room.roomCode }"
        :disabled="disabled || (guest && room.allowsGuests === false)"
        @click="selectRoom(room)"
      >
        <AvatarImage class="spectator-room-avatar" :src="room.hostAvatarUrl" :name="room.hostName" />
        <span><strong>{{ room.roomName || `${room.hostName}的房间` }}</strong><small>{{ room.roomCode }} · {{ room.playerCount }} 名玩家 · {{ room.spectatorCount ?? 0 }} 人观战</small></span>
        <Eye :size="17" />
      </button>
    </div>
    <p v-else class="spectator-room-empty"><UsersRound :size="18" />暂时没有公开且正在进行的 {{ gameName }} 对局</p>

    <form class="spectator-code-search" @submit.prevent="inspectRoom">
      <label><span>通过房间码观战</span><input v-model="roomCode" maxlength="8" placeholder="输入 4–8 位房间码" autocomplete="off" autocapitalize="characters" /></label>
      <button type="submit" data-ui-interaction="lift" :disabled="disabled || roomCode.trim().length < 4 || arcade.busy"><Search :size="16" />查找</button>
    </form>

    <section v-if="selectedRoom" class="spectator-targets">
      <header><span><strong>选择观战视角</strong><small>{{ selectedRoom.roomName || `房间 ${selectedRoom.roomCode}` }} · 本局选定后不能切换</small></span></header>
      <div>
        <button
          v-for="player in targets"
          :key="player.id"
          type="button"
          data-ui-interaction="choice"
          :disabled="disabled || arcade.busy"
          @click="watchPlayer(player.id)"
        >
          <AvatarImage class="spectator-target-avatar" :src="player.avatarUrl" :name="player.name" />
          <span><strong>{{ player.name }}</strong><small>{{ player.seat + 1 }} 号位 · {{ player.connected ? '在线' : '暂时离线' }}</small></span>
          <b>观看</b>
        </button>
      </div>
    </section>

    <p v-if="disabled" class="spectator-disabled">请先返回并退出当前房间，再进入其他对局观战。</p>
  </section>
</template>

<style scoped>
.spectator-browser { width: min(100%, 760px); display: grid; gap: 14px; margin: 18px auto 0; padding: 17px; }
.spectator-browser > header { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 11px; }
.spectator-browser > header > span:nth-child(2),.spectator-targets header span { min-width: 0; display: grid; gap: 2px; }
.spectator-browser header small { color: var(--muted); font-size: 11px; }
.spectator-browser > header > b { display: inline-flex; align-items: center; gap: 5px; border-radius: 999px; padding: 5px 8px; color: var(--accent); background: color-mix(in srgb, var(--accent) 9%, transparent); font-size: 10px; }
.spectator-browser-icon { width: 40px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 12px; color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, var(--surface-inset)); }
.spectator-room-list,.spectator-targets > div { display: grid; gap: 8px; }
.spectator-room-list button,.spectator-targets button { min-width: 0; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 10px; border: 1px solid var(--line); border-radius: 13px; padding: 10px 11px; color: var(--text); background: var(--surface-inset); text-align: left; cursor: pointer; }
.spectator-room-list button.selected { border-color: color-mix(in srgb, var(--accent) 55%, var(--line)); background: color-mix(in srgb, var(--accent) 7%, var(--surface-inset)); }
.spectator-room-list button:disabled,.spectator-targets button:disabled { cursor: not-allowed; opacity: .48; }
.spectator-room-list button > span,.spectator-targets button > span { min-width: 0; display: grid; gap: 2px; }
.spectator-room-list small,.spectator-targets small { overflow: hidden; color: var(--muted); font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.spectator-room-avatar,.spectator-target-avatar { width: 36px; height: 36px; }
.spectator-room-empty { display: flex; align-items: center; justify-content: center; gap: 8px; border: 1px dashed var(--line); border-radius: 12px; padding: 14px; color: var(--muted); font-size: 11px; }
.spectator-code-search { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: end; gap: 9px; border-top: 1px solid var(--line); padding-top: 14px; }
.spectator-code-search label { display: grid; gap: 6px; color: var(--muted); font-size: 10px; font-weight: 800; }
.spectator-code-search input { min-height: 42px; border: 1px solid var(--line); border-radius: 10px; padding: 0 12px; color: var(--text); background: var(--surface-inset); text-transform: uppercase; }
.spectator-code-search button { min-height: 42px; display: inline-flex; align-items: center; gap: 6px; border: 1px solid color-mix(in srgb, var(--accent) 34%, var(--line)); border-radius: 10px; padding: 0 14px; color: var(--accent); background: color-mix(in srgb, var(--accent) 7%, var(--surface)); font-weight: 850; }
.spectator-targets { display: grid; gap: 10px; border: 1px solid color-mix(in srgb, var(--accent) 22%, var(--line)); border-radius: 14px; padding: 12px; background: color-mix(in srgb, var(--accent) 4%, var(--surface-inset)); }
.spectator-targets button b { border-radius: 999px; padding: 5px 9px; color: var(--accent-contrast); background: var(--accent); font-size: 10px; }
.spectator-disabled { color: #e9a19c; font-size: 11px; text-align: center; }
@media (max-width: 600px) {
  .spectator-browser { padding: 14px; }
  .spectator-browser > header { grid-template-columns: auto minmax(0, 1fr); }.spectator-browser > header > b { grid-column: 1 / -1; width: fit-content; }
  .spectator-code-search { grid-template-columns: 1fr; }.spectator-code-search button { justify-content: center; }
}
</style>
