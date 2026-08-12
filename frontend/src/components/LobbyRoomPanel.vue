<script setup lang="ts">
import { ChevronRight, Radio, UsersRound } from '@lucide/vue'
import type { ArcadeLobbyRoom } from '../types/arcade'
import AvatarImage from './AvatarImage.vue'

defineProps<{
  rooms: ArcadeLobbyRoom[]
  connected: boolean
}>()

defineEmits<{
  open: [room: ArcadeLobbyRoom]
}>()
</script>

<template>
  <section class="lobby-room-panel surface" aria-label="实时房间">
    <header class="lobby-room-heading">
      <span>
        <small>公开房间</small>
        <strong>实时房间</strong>
      </span>
      <b :class="{ offline: !connected }"><i />{{ connected ? '在线' : '重连中' }}</b>
    </header>

    <div v-if="rooms.length" class="lobby-room-list">
      <button
        v-for="room in rooms"
        :key="room.roomCode"
        type="button"
        class="lobby-room-row"
        @click="$emit('open', room)"
      >
        <AvatarImage class="lobby-room-avatar" :src="room.hostAvatarUrl" :name="room.hostName" />
        <span class="lobby-room-copy">
          <strong>{{ room.roomName || `${room.hostName}的房间` }}</strong>
          <small>{{ room.gameName }} · {{ room.phase === 'lobby' ? '等待加入' : '对局进行中' }}</small>
        </span>
        <span class="lobby-room-count"><UsersRound :size="13" />{{ room.playerCount }}/{{ room.maxPlayers }}</span>
        <ChevronRight :size="16" />
      </button>
    </div>

    <div v-else class="lobby-room-empty">
      <span><Radio :size="22" /></span>
      <strong>当前没有公开房间</strong>
      <small>进入任意多人游戏创建房间后，会在这里显示。</small>
    </div>

    <footer>
      <span><i />大厅信号实时同步</span>
      <small>{{ rooms.length }} 个活跃房间</small>
    </footer>
  </section>
</template>

<style scoped>
.lobby-room-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  min-width: 0;
  overflow: hidden;
  padding: 16px;
}

.lobby-room-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 48px;
  border-bottom: 1px solid var(--line);
  padding: 0 2px 13px;
}

.lobby-room-heading > span {
  display: grid;
  gap: 3px;
}

.lobby-room-heading small {
  color: var(--gold);
  font-size: 9px;
  font-weight: 780;
}

.lobby-room-heading strong {
  font-size: 16px;
}

.lobby-room-heading > b {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--green);
  font-size: 9px;
}

.lobby-room-heading > b i,
.lobby-room-panel footer i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 8px color-mix(in srgb, var(--green) 48%, transparent);
}

.lobby-room-heading > b.offline {
  color: var(--red);
}

.lobby-room-heading > b.offline i {
  background: var(--red);
  box-shadow: none;
}

.lobby-room-list {
  display: grid;
  align-content: start;
}

.lobby-room-row {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 9px;
  width: 100%;
  min-width: 0;
  min-height: 67px;
  border: 0;
  border-bottom: 1px solid var(--line);
  padding: 8px 2px;
  color: var(--text);
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.lobby-room-avatar {
  width: 34px;
  aspect-ratio: 1;
  border: 1px solid var(--line-strong);
  border-radius: 50%;
  background: var(--surface-soft);
}

.lobby-room-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.lobby-room-copy strong,
.lobby-room-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lobby-room-copy strong {
  font-size: 12px;
}

.lobby-room-copy small {
  color: var(--muted);
  font-size: 9px;
}

.lobby-room-count {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--text-soft);
  font-size: 9px;
}

.lobby-room-row > svg {
  color: var(--muted);
}

.lobby-room-empty {
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  min-height: 180px;
  color: var(--muted);
  text-align: center;
}

.lobby-room-empty > span {
  display: grid;
  place-items: center;
  width: 48px;
  aspect-ratio: 1;
  border: 1px solid var(--line-strong);
  border-radius: 50%;
  color: var(--gold);
  background: var(--surface-inset);
  box-shadow: var(--shadow-contact);
}

.lobby-room-empty strong {
  color: var(--text-soft);
  font-size: 12px;
}

.lobby-room-empty small {
  max-width: 220px;
  font-size: 9px;
  line-height: 1.6;
}

.lobby-room-panel footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 13px 2px 0;
  color: var(--muted);
  font-size: 8px;
}

.lobby-room-panel footer span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

@media (hover: hover) {
  .lobby-room-row:hover {
    padding-right: 6px;
    padding-left: 6px;
    color: var(--gold);
    background: color-mix(in srgb, var(--gold) 5%, transparent);
  }

  .lobby-room-row:hover > svg {
    color: var(--gold);
    transform: translateX(2px);
  }
}

@media (max-width: 680px) {
  .lobby-room-panel {
    padding: 13px;
  }

  .lobby-room-row {
    grid-template-columns: 34px minmax(0, 1fr) auto;
  }

  .lobby-room-count {
    display: none;
  }
}
</style>
