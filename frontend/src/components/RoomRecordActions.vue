<script setup lang="ts">
import { ref } from 'vue'
import { History, Trophy } from '@lucide/vue'
import LeaderboardModal from './LeaderboardModal.vue'
import StatsModal from './StatsModal.vue'
import UiButton from './ui/UiButton.vue'

const props = defineProps<{
  accountId?: string
  gameKey: string
  gameName: string
  gameMode?: string
  guest?: boolean
}>()

const showStats = ref(false)
const showLeaderboard = ref(false)
</script>

<template>
  <UiButton
    v-if="!props.guest"
    compact
    class="room-record-action"
    aria-label="查看我的战绩"
    @click="showStats = true"
  >
    <History :size="18" />
    <span>我的战绩</span>
  </UiButton>
  <UiButton
    compact
    class="room-record-action"
    aria-label="查看排行榜"
    @click="showLeaderboard = true"
  >
    <Trophy :size="18" />
    <span>排行榜</span>
  </UiButton>

  <StatsModal
    v-if="showStats && !props.guest"
    :game-key="props.gameKey"
    :game-name="props.gameName"
    :game-mode="props.gameMode"
    @close="showStats = false"
  />
  <LeaderboardModal
    v-if="showLeaderboard"
    :account-id="props.accountId ?? ''"
    :game-key="props.gameKey"
    :game-name="props.gameName"
    :game-mode="props.gameMode"
    @close="showLeaderboard = false"
  />
</template>

<style scoped>
.room-record-action {
  min-width: 112px;
  font-size: 12px;
  white-space: nowrap;
}

.room-record-action > svg {
  flex: 0 0 auto;
}

@media (max-width: 680px) {
  .room-record-action {
    flex: 1 1 calc(50% - 4px);
    min-width: 0;
  }
}
</style>
