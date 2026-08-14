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
