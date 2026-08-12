<script setup lang="ts">
import { computed } from 'vue'
import { Crown, Eye, WifiOff } from '@lucide/vue'
import AvatarImage from './AvatarImage.vue'

const props = withDefaults(defineProps<{
  avatarUrl?: string | null
  name: string
  seat: number
  host?: boolean
  bot?: boolean
  botDifficulty?: string
  guest?: boolean
  connected?: boolean
  leftRoom?: boolean
  disconnectForfeited?: boolean
  disconnectForfeitAt?: string | null
  self?: boolean
  perspective?: boolean
}>(), {
  avatarUrl: null,
  host: false,
  bot: false,
  botDifficulty: '',
  guest: false,
  connected: true,
  leftRoom: false,
  disconnectForfeited: false,
  disconnectForfeitAt: null,
  self: false,
  perspective: false,
})

const statusLabel = computed(() => {
  if (props.leftRoom) return '已退出'
  if (props.connected) return '在线'
  if (props.disconnectForfeited) return '掉线弃权'
  if (props.disconnectForfeitAt) return '离线，10 分钟后弃权'
  return '离线'
})
</script>

<template>
  <article
    class="room-player-seat"
    :class="{
      'room-player-seat--self': self,
      'room-player-seat--perspective': perspective,
      'room-player-seat--offline': !connected || leftRoom,
    }"
  >
    <span class="room-player-seat-number">{{ seat + 1 }}</span>
    <span class="room-player-seat-avatar-wrap">
      <AvatarImage
        class="room-player-seat-avatar"
        :src="avatarUrl"
        :name="name"
        :fallback="seat + 1"
      />
      <i :class="{ offline: !connected }" aria-hidden="true" />
    </span>

    <span class="room-player-seat-copy">
      <strong>{{ name }}</strong>
      <small>
        <Crown v-if="host" :size="12" />
        <Eye v-else-if="perspective" :size="12" />
        <WifiOff v-else-if="!connected" :size="12" />
        {{ bot ? `AI · ${botDifficulty || '普通'}` : host ? '房主' : '玩家' }}
        <template v-if="guest"> · 游客</template>
        <template v-if="perspective"> · 观战视角</template>
      </small>
    </span>

    <span class="room-player-seat-status" :class="{ offline: !connected }">
      {{ statusLabel }}
    </span>

    <span v-if="$slots.actions" class="room-player-seat-actions">
      <slot name="actions" />
    </span>
  </article>
</template>

<style scoped>
.room-player-seat {
  position: relative;
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr) auto;
  flex: 0 0 var(--player-card-width);
  align-items: center;
  gap: 10px;
  min-width: 0;
  min-height: 76px;
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  padding: 10px 11px;
  background: var(--surface-glass, var(--surface-elevated));
  box-shadow: var(--shadow-contact, 0 5px 18px rgba(0, 0, 0, .16));
}

.room-player-seat::after {
  position: absolute;
  inset: 1px;
  border: 1px solid color-mix(in srgb, white 32%, transparent);
  border-radius: calc(var(--radius-card) - 2px);
  content: '';
  pointer-events: none;
}

.room-player-seat--self,
.room-player-seat--perspective {
  border-color: color-mix(in srgb, var(--gold) 56%, var(--line));
  box-shadow:
    inset 3px 0 0 var(--gold),
    var(--shadow-contact, 0 5px 18px rgba(0, 0, 0, .16));
}

.room-player-seat--offline {
  opacity: .66;
}

.room-player-seat-number {
  display: grid;
  place-items: center;
  width: 25px;
  height: 25px;
  border: 1px solid var(--line);
  border-radius: 50%;
  color: var(--muted);
  background: var(--surface-inset);
  font-size: 10px;
  font-weight: 850;
}

.room-player-seat-avatar-wrap {
  position: relative;
  width: 42px;
  height: 42px;
}

.room-player-seat-avatar {
  width: 100%;
  height: 100%;
  border: 1px solid color-mix(in srgb, var(--gold) 26%, var(--line));
  border-radius: 50%;
  background: var(--surface-raised);
  box-shadow: var(--shadow-contact, 0 4px 12px rgba(0, 0, 0, .14));
}

.room-player-seat-avatar-wrap > i {
  position: absolute;
  right: -1px;
  bottom: 0;
  width: 10px;
  height: 10px;
  border: 2px solid var(--surface-elevated);
  border-radius: 50%;
  background: var(--green);
}

.room-player-seat-avatar-wrap > i.offline {
  background: var(--muted);
}

.room-player-seat-copy {
  min-width: 0;
}

.room-player-seat-copy strong,
.room-player-seat-copy small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-player-seat-copy strong {
  font-size: 13px;
}

.room-player-seat-copy small {
  margin-top: 4px;
  color: var(--muted);
  font-size: 9px;
}

.room-player-seat-copy svg {
  color: var(--gold);
  vertical-align: -2px;
}

.room-player-seat-status {
  border: 1px solid color-mix(in srgb, var(--green) 24%, var(--line));
  border-radius: 999px;
  padding: 5px 7px;
  color: var(--green);
  background: color-mix(in srgb, var(--green) 8%, transparent);
  font-size: 8px;
  font-weight: 800;
  white-space: nowrap;
}

.room-player-seat-status.offline {
  border-color: var(--line);
  color: var(--muted);
  background: var(--surface-inset);
}

.room-player-seat-actions {
  display: flex;
}

@container (max-width: 500px) {
  .room-player-seat {
    grid-template-columns: auto auto minmax(0, 1fr);
  }

  .room-player-seat-status,
  .room-player-seat-actions {
    grid-column: 2 / -1;
    justify-self: start;
  }
}
</style>
