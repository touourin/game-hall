<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { LoaderCircle, Trophy } from '@lucide/vue'
import { leaderboardPresentation } from '../game-platform/records'
import { loadLeaderboard, type LeaderboardEntry } from '../stats'
import AvatarImage from './AvatarImage.vue'
import BaseModal from './ui/BaseModal.vue'

const props = defineProps<{ accountId: string; gameKey: string; gameName: string; gameMode?: string }>()
defineEmits<{ close: [] }>()

const players = ref<LeaderboardEntry[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const presentation = leaderboardPresentation(props.gameKey)
const activeGameMode = ref<string | undefined>(props.gameMode ?? presentation.defaultMode)
const activeGameVariant = ref<string | undefined>(
  presentation.defaultVariant?.(activeGameMode.value),
)

function selectFilter(mode: string, variant?: string) {
  activeGameMode.value = mode
  activeGameVariant.value = variant
}

async function loadPlayers() {
  loading.value = true
  error.value = null
  try {
    players.value = await loadLeaderboard(
      props.gameKey,
      activeGameMode.value,
      activeGameVariant.value,
    )
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '读取排行榜失败'
  } finally {
    loading.value = false
  }
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
    inline
    @close="$emit('close')"
  >
      <span class="modal-icon"><Trophy :size="25" /></span>
      <h2>
        {{ props.gameName }}{{ presentation.titleSuffix?.(activeGameMode, activeGameVariant) ?? '' }}排行榜
      </h2>
      <p>{{ presentation.description }}</p>

      <div
        v-if="presentation.filters?.length && !props.gameMode"
        class="stats-mode-tabs"
        role="group"
        :aria-label="`筛选${props.gameName}模式排行榜`"
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
      <p v-if="error" class="account-error" role="alert">{{ error }}</p>
  </BaseModal>
</template>

<style scoped>
.leaderboard-list > div {
  grid-template-columns: auto auto minmax(0, 1fr) auto;
}

.leaderboard-avatar {
  width: 39px;
  height: 39px;
  border: 1px solid color-mix(in srgb, var(--gold) 30%, var(--line));
  border-radius: 50%;
  background: var(--surface-inset);
  box-shadow: var(--shadow-contact);
}
</style>
