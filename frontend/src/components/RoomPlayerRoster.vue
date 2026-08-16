<script setup lang="ts">
import { computed } from 'vue'
import type { ArcadeAiConfig, ArcadePlayer } from '../types/arcade'
import RoomAiSeatControl from './RoomAiSeatControl.vue'
import RoomKickButton from './RoomKickButton.vue'
import RoomPlayerSeat from './RoomPlayerSeat.vue'

const props = withDefaults(defineProps<{
  players: ArcadePlayer[]
  selfId: string
  perspectivePlayerId?: string | null
  canKickPlayers?: boolean
  canAddAiPlayer?: boolean
  availableSeats?: number
  ai?: ArcadeAiConfig | null
  busy?: boolean
}>(), {
  perspectivePlayerId: null,
  canKickPlayers: false,
  canAddAiPlayer: false,
  availableSeats: 0,
  ai: null,
  busy: false,
})

const emit = defineEmits<{
  kick: [playerId: string]
  addAi: [difficulty: string]
}>()

const columns = computed(() => {
  const playerCount = props.players.length + (props.canAddAiPlayer ? 1 : 0)
  if (playerCount <= 5) return Math.max(1, playerCount)
  if (playerCount === 6) return 3
  return Math.ceil(playerCount / 2)
})

const stripStyle = computed(() => {
  const widthPercent = Number((100 / columns.value).toFixed(6))
  const gapCorrection = Number((10 * (columns.value - 1) / columns.value).toFixed(3))
  return {
    '--player-card-width': `calc(${widthPercent}% - ${gapCorrection}px)`,
  }
})

function aiDifficultyLabel(difficulty?: string | null): string {
  if (!difficulty) return '普通'
  return props.ai?.difficulties.find(
    (option) => option.key === difficulty,
  )?.label ?? difficulty
}
</script>

<template>
  <section
    class="surface arcade-player-strip"
    :data-player-columns="columns"
    :style="stripStyle"
    aria-label="房间玩家"
  >
    <RoomPlayerSeat
      v-for="player in players"
      :key="player.id"
      :avatar-url="player.avatarUrl"
      :name="player.name"
      :seat="player.seat"
      :host="player.isHost"
      :bot="player.isBot"
      :bot-difficulty="aiDifficultyLabel(player.botDifficulty)"
      :guest="player.isGuest"
      :connected="player.connected"
      :left-room="player.leftRoom"
      :disconnect-forfeited="player.disconnectForfeited"
      :disconnect-forfeit-at="player.disconnectForfeitAt"
      :self="player.id === selfId"
      :perspective="player.id === perspectivePlayerId"
    >
      <template v-if="canKickPlayers && player.id !== selfId" #actions>
        <RoomKickButton
          :player-name="player.name"
          :busy="busy"
          @confirm="emit('kick', player.id)"
        />
      </template>
    </RoomPlayerSeat>
    <RoomAiSeatControl
      v-if="canAddAiPlayer"
      :config="ai"
      :available-seats="availableSeats"
      :busy="busy"
      @add="emit('addAi', $event)"
    />
  </section>
</template>

<style scoped>
.arcade-player-strip {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-bottom: 24px;
  padding: 43px 14px 14px;
  border-color: color-mix(in srgb, var(--line-strong) 65%, var(--line));
}

.arcade-player-strip::before {
  position: absolute;
  top: 14px;
  right: 16px;
  left: 16px;
  height: 17px;
  border-bottom: 1px solid var(--instrument-line);
  color: var(--accent);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: .08em;
  content: '房间座位  ·  SEAT ARRAY';
}

.arcade-player-strip::after {
  position: absolute;
  inset: 4px;
  border: 1px solid color-mix(in srgb, var(--line-bright) 11%, transparent);
  border-radius: calc(var(--radius-panel) - 4px);
  content: '';
  pointer-events: none;
}

@media (max-width: 860px) {
  .arcade-player-strip > :deep(.room-player-seat) {
    flex-basis: calc(33.333333% - 6.667px);
  }
}

@media (max-width: 620px), (orientation: landscape) and (max-height: 600px) and (max-width: 980px) {
  .arcade-player-strip > :deep(.room-player-seat) {
    flex-basis: calc(50% - 5px);
  }
}

@media (max-width: 430px) {
  .arcade-player-strip > :deep(.room-player-seat) {
    flex-basis: 100%;
  }
}
</style>
