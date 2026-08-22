<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { LoaderCircle, Trophy } from '@lucide/vue'
import { useLatestAsyncResource } from '../composables/useLatestAsyncResource'
import { leaderboardPresentation } from '../game-platform/records'
import { loadLeaderboard, type LeaderboardEntry } from '../stats'
import AvatarImage from './AvatarImage.vue'
import BaseModal from './ui/BaseModal.vue'

const props = withDefaults(defineProps<{
  accountId: string
  gameKey: string
  gameName: string
  gameMode?: string
  fixedGameMode?: boolean
}>(), {
  fixedGameMode: false,
})
defineEmits<{ close: [] }>()

const presentation = leaderboardPresentation(props.gameKey)
const activeGameMode = ref<string | undefined>(props.gameMode ?? presentation.defaultMode)
const activeGameVariant = ref<string | undefined>(
  presentation.defaultVariant?.(activeGameMode.value),
)
const {
  data: players,
  loading,
  error,
  execute: executeLoad,
} = useLatestAsyncResource<LeaderboardEntry[]>(() => [], '读取排行榜失败')

function selectFilter(mode: string, variant?: string) {
  activeGameMode.value = mode
  activeGameVariant.value = variant
}

function loadPlayers() {
  return executeLoad(() => loadLeaderboard(
    props.gameKey,
    activeGameMode.value,
    activeGameVariant.value,
  ))
}

onMounted(loadPlayers)
watch([activeGameMode, activeGameVariant], loadPlayers)
</script>

<template>
  <BaseModal
    aria-label="排行榜"
    panel-class="leaderboard-modal"
    close-label="关闭排行榜"
    mobile-sheet
    @close="$emit('close')"
  >
      <span class="modal-icon"><Trophy :size="25" /></span>
      <h2>
        {{ props.gameName }}{{ presentation.titleSuffix?.(activeGameMode, activeGameVariant) ?? '' }}排行榜
      </h2>
      <p>{{ presentation.description }}</p>

      <div
        v-if="presentation.filters?.length && !props.fixedGameMode"
        class="stats-mode-tabs"
        role="group"
        :aria-label="`筛选${props.gameName}模式排行榜`"
        :style="{ '--stats-mode-columns': Math.min(presentation.filters.length, 4) }"
      >
        <button
          v-for="filter in presentation.filters"
          :key="`${filter.mode}-${filter.variant ?? 'default'}`"
          type="button"
          data-ui-interaction="choice"
          :class="{
            active:
              activeGameMode === filter.mode &&
              activeGameVariant === filter.variant,
          }"
          @click="selectFilter(filter.mode, filter.variant)"
        >
          {{ filter.label }}
        </button>
      </div>

      <div v-if="loading" class="stats-loading">
        <LoaderCircle :size="24" /> 正在读取排行…
      </div>
      <div v-else-if="error" class="account-error leaderboard-error" role="alert">
        {{ error }}
      </div>
      <ol v-else-if="players.length" class="leaderboard-list">
        <li
          v-for="player in players"
          :key="player.accountId"
          class="leaderboard-entry"
          :class="{ self: player.accountId === props.accountId }"
        >
          <b class="leaderboard-rank" :class="`rank-${player.rank}`">{{ player.rank }}</b>
          <AvatarImage
            class="leaderboard-avatar"
            :src="player.avatarUrl"
            :name="player.playerName"
          />
          <span class="leaderboard-identity">
            <strong>{{ player.playerName }}</strong>
            <small>{{ presentation.entryDetail(player) }}</small>
          </span>
          <em class="leaderboard-score">{{ presentation.entryScore(player) }}</em>
        </li>
      </ol>
      <div v-else class="stats-empty">还没有符合条件的真人对局</div>
      <p class="leaderboard-note">{{ presentation.note }}</p>
  </BaseModal>
</template>

<style scoped>
.leaderboard-error {
  margin: 16px 0;
}
</style>
