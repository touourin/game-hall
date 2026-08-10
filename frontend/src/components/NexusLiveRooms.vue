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
  <section class="nexus-live-rooms surface" aria-label="实时房间">
    <header class="nexus-panel-heading">
      <span><small>LIVE SIGNAL</small><strong>实时房间</strong></span>
      <b :class="{ offline: !connected }"><i />{{ connected ? 'ONLINE' : 'RECONNECTING' }}</b>
    </header>

    <div v-if="rooms.length" class="nexus-room-list">
      <button
        v-for="room in rooms"
        :key="room.roomCode"
        type="button"
        class="nexus-room-row"
        @click="$emit('open', room)"
      >
        <span class="nexus-room-code">{{ room.roomCode.slice(0, 4) }}</span>
        <AvatarImage class="nexus-room-avatar" :src="room.hostAvatarUrl" :name="room.hostName" />
        <span class="nexus-room-copy">
          <strong>{{ room.roomName || `${room.hostName}的房间` }}</strong>
          <small>{{ room.gameName }} · {{ room.phase === 'lobby' ? '等待加入' : '对局进行中' }}</small>
        </span>
        <span class="nexus-room-count"><UsersRound :size="13" />{{ room.playerCount }}/{{ room.maxPlayers }}</span>
        <ChevronRight :size="16" />
      </button>
    </div>

    <div v-else class="nexus-room-empty">
      <span><Radio :size="22" /></span>
      <strong>当前没有公开房间</strong>
      <small>选择游戏创建房间后，会在这里显示真实对局信号。</small>
    </div>

    <footer>
      <span><i />大厅信号实时同步</span>
      <small>{{ rooms.length }} ACTIVE ROOMS</small>
    </footer>
  </section>
</template>

<style scoped>
.nexus-live-rooms { min-width: 0; overflow: hidden; padding: 14px; }
.nexus-panel-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 45px; border-bottom: 1px solid var(--line); padding: 0 2px 12px; }
.nexus-panel-heading > span { min-width: 0; display: grid; gap: 3px; }.nexus-panel-heading small { color: var(--gold); font-family: ui-monospace,"SFMono-Regular",Consolas,monospace; font-size: 7px; font-weight: 800; letter-spacing: .18em; }.nexus-panel-heading strong { font-size: 15px; }
.nexus-panel-heading > b { flex: 0 0 auto; display: inline-flex; align-items: center; gap: 5px; color: var(--green); font-family: ui-monospace,"SFMono-Regular",Consolas,monospace; font-size: 6px; font-weight: 800; letter-spacing: .08em; }.nexus-panel-heading > b i,.nexus-live-rooms footer i { width: 6px; height: 6px; border-radius: 50%; background: var(--green); box-shadow: 0 0 9px var(--green); }.nexus-panel-heading > b.offline { color: var(--red); }.nexus-panel-heading > b.offline i { background: var(--red); box-shadow: 0 0 9px var(--red); }
.nexus-room-list { display: grid; }
.nexus-room-row { position: relative; width: 100%; min-width: 0; min-height: 72px; display: grid; grid-template-columns: 27px 34px minmax(0,1fr) auto auto; align-items: center; gap: 8px; border: 0; border-bottom: 1px solid var(--line); padding: 8px 2px; color: var(--text); background: transparent; text-align: left; cursor: pointer; }
.nexus-room-code { color: color-mix(in srgb, var(--accent-secondary) 75%, var(--muted)); font-family: ui-monospace,"SFMono-Regular",Consolas,monospace; font-size: 7px; }
.nexus-room-avatar { width: 32px; aspect-ratio: 1; border: 1px solid color-mix(in srgb, var(--gold) 30%, var(--line)); border-radius: 4px; color: var(--gold); background: var(--surface-soft); font-size: 9px; font-weight: 850; }
.nexus-room-copy { min-width: 0; display: grid; gap: 4px; }.nexus-room-copy strong,.nexus-room-copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.nexus-room-copy strong { font-size: 11px; }.nexus-room-copy small { color: var(--muted); font-size: 7px; }
.nexus-room-count { display: inline-flex; align-items: center; gap: 3px; color: var(--text-soft); font-size: 7px; }.nexus-room-row > svg { color: var(--muted); }
.nexus-room-empty { min-height: 250px; display: grid; place-items: center; align-content: center; gap: 8px; color: var(--muted); text-align: center; }.nexus-room-empty > span { display:grid; width:46px; aspect-ratio:1; place-items:center; border:1px solid var(--line-strong); border-radius:50%; color:var(--gold); background:color-mix(in srgb,var(--gold) 7%,transparent); box-shadow:var(--glow-primary); }.nexus-room-empty strong { color: var(--text-soft); font-size: 11px; }.nexus-room-empty small { max-width: 210px; font-size: 8px; line-height: 1.5; }
.nexus-live-rooms footer { display:flex; align-items:center; justify-content:space-between; gap:10px; padding:12px 2px 0; color:var(--muted); font-family:ui-monospace,"SFMono-Regular",Consolas,monospace; font-size:6px; }.nexus-live-rooms footer span { display:inline-flex; align-items:center; gap:6px; }.nexus-live-rooms footer i { width:5px; height:5px; }
@media (hover:hover) { .nexus-room-row:hover { padding-right:6px; padding-left:6px; color:var(--gold); background:color-mix(in srgb,var(--gold) 5%,transparent); }.nexus-room-row:hover > svg { color:var(--gold); transform:translateX(2px); } }
@media (max-width:680px) { .nexus-live-rooms { padding:12px; }.nexus-room-row { min-height:65px; grid-template-columns:26px 31px minmax(0,1fr) auto; }.nexus-room-count { display:none; }.nexus-room-row > svg { width:14px; }.nexus-room-empty { min-height:160px; } }
</style>
