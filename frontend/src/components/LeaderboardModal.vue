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
      <div v-else-if="players.length" class="leaderboard-list">
        <div
          v-for="player in players"
          :key="player.accountId"
          :class="{ self: player.accountId === props.accountId }"
        >
          <b :class="`rank-${player.rank}`">{{ player.rank }}</b>
          <AvatarImage
            class="leaderboard-avatar"
            :src="player.avatarUrl"
            :name="player.playerName"
          />
          <span>
            <strong>{{ player.playerName }}</strong>
            <small>{{ presentation.entryDetail(player) }}</small>
          </span>
          <em>{{ presentation.entryScore(player) }}</em>
        </div>
      </div>
      <div v-else class="stats-empty">还没有符合条件的真人对局</div>
      <p class="leaderboard-note">{{ presentation.note }}</p>
  </BaseModal>
</template>

<style scoped>
.leaderboard-list > div {
  grid-template-areas: "rank avatar identity score";
  grid-template-columns: auto auto minmax(0, 1fr) auto;
}

.leaderboard-list > div > b {
  grid-area: rank;
}

.leaderboard-list > div > span {
  grid-area: identity;
}

.leaderboard-list > div > em {
  grid-area: score;
  justify-self: end;
  font-variant-numeric: tabular-nums;
  text-align: right;
  white-space: nowrap;
}

.leaderboard-list small {
  overflow-wrap: anywhere;
}

.leaderboard-avatar {
  grid-area: avatar;
  width: 39px;
  height: 39px;
  border: 1px solid color-mix(in srgb, var(--accent) 30%, var(--line));
  border-radius: 50%;
  background: var(--surface-inset);
  box-shadow: var(--shadow-contact);
}

.leaderboard-error {
  margin: 16px 0;
}

@media (max-width: 420px) {
  .leaderboard-list > div {
    grid-template-areas:
      "rank avatar identity"
      "rank avatar score";
    grid-template-columns: auto auto minmax(0, 1fr);
    row-gap: 3px;
  }

  .leaderboard-list > div > em {
    justify-self: start;
  }
}
</style>
