<script setup lang="ts">
import { ref } from 'vue'
import { History, Trophy } from '@lucide/vue'
import LeaderboardModal from './LeaderboardModal.vue'
import StatsModal from './StatsModal.vue'

const props = defineProps<{
  accountId?: string
  gameKey: string
  gameName: string
  gameMode?: string
}>()

const showStats = ref(false)
const showLeaderboard = ref(false)
</script>

<template>
  <button
    type="button"
    class="header-action room-record-action"
    aria-label="查看我的战绩"
    @click="showStats = true"
  >
    <History :size="18" />
    <span>我的战绩</span>
  </button>
  <button
    type="button"
    class="header-action room-record-action"
    aria-label="查看排行榜"
    @click="showLeaderboard = true"
  >
    <Trophy :size="18" />
    <span>排行榜</span>
  </button>

  <StatsModal
    v-if="showStats"
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
  display: inline-flex;
  width: auto;
  min-width: 112px;
  height: 42px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 12px;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}

.room-record-action > svg {
  flex: 0 0 auto;
}

@media (hover: hover) {
  .room-record-action:hover {
    border-color: var(--line-strong);
    color: var(--gold);
    background: var(--surface-soft);
  }
}

@media (max-width: 680px) {
  .room-record-action {
    flex: 1 1 calc(50% - 4px);
    min-width: 0;
  }
}
</style>
