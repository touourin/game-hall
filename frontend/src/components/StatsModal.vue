<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { History, LoaderCircle } from '@lucide/vue'
import { builtinGameDefinition } from '../game-platform/registry'
import { statsPresentation } from '../game-platform/records'
import BackNavigationButton from './BackNavigationButton.vue'
import DefaultMatchDetail from './DefaultMatchDetail.vue'
import MatchMetricDetail from './MatchMetricDetail.vue'
import BaseModal from './ui/BaseModal.vue'
import {
  loadMatchDetail,
  loadPersonalStats,
  type MatchDetail,
  type MatchHistoryItem,
  type StatsSummary,
} from '../stats'

const props = defineProps<{ gameKey?: string; gameName?: string; gameMode?: string }>()
defineEmits<{ close: [] }>()

const summary = ref<StatsSummary | null>(null)
const history = ref<MatchHistoryItem[]>([])
const selectedMatch = ref<MatchDetail | null>(null)
const loading = ref(true)
const detailLoading = ref(false)
const error = ref<string | null>(null)
const presentation = statsPresentation(props.gameKey)
const activeGameMode = ref<string | undefined>(props.gameMode ?? presentation.defaultMode)
const activeGameVariant = ref<string | undefined>(
  presentation.defaultVariant?.(activeGameMode.value),
)
const selectedMatchPresentation = computed(() =>
  statsPresentation(selectedMatch.value?.gameKey ?? props.gameKey),
)
const selectedMatchDetailSection = computed(() => {
  const match = selectedMatch.value
  if (!match) return null
  return selectedMatchPresentation.value.detailSection?.(match) ?? null
})
const selectedMatchDetailComponent = computed(() => {
  if (!selectedMatch.value) return null
  return builtinGameDefinition(selectedMatch.value.gameKey)?.records?.matchDetailComponent
    ?? null
})

function historyPresentation(match: MatchHistoryItem) {
  return props.gameKey ? presentation : statsPresentation(match.gameKey)
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function selectFilter(mode: string, variant?: string) {
  activeGameMode.value = mode
  activeGameVariant.value = variant
}

async function openMatch(matchId: string) {
  detailLoading.value = true
  error.value = null
  try {
    selectedMatch.value = await loadMatchDetail(matchId)
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '读取战绩失败'
  } finally {
    detailLoading.value = false
  }
}

async function loadStats() {
  loading.value = true
  error.value = null
  try {
    const data = await loadPersonalStats(
      props.gameKey,
      activeGameMode.value,
      activeGameVariant.value,
    )
    summary.value = data.summary
    history.value = data.history
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '读取战绩失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
watch([activeGameMode, activeGameVariant], loadStats)
</script>

<template>
  <BaseModal
    aria-label="战绩"
    panel-class="stats-modal"
    close-label="关闭战绩"
    mobile-sheet
    inline
    @close="$emit('close')"
  >

      <template v-if="selectedMatch">
        <BackNavigationButton
          class="stats-back"
          label="返回战绩列表"
          @click="selectedMatch = null"
        />
        <span class="modal-icon"><History :size="24" /></span>
        <h2>{{ selectedMatch.gameName }} · 房间 {{ selectedMatch.roomCode }}</h2>
        <p>{{ formatDate(selectedMatch.endedAt) }} · {{ selectedMatch.playerCount }} 人局</p>
        <p v-if="selectedMatchPresentation.detailModeLabel" class="match-mode-label">
          {{ selectedMatchPresentation.detailModeLabel(selectedMatch) }}
        </p>

        <div class="match-detail-result" :class="selectedMatch.winner">
          <strong>{{ selectedMatchPresentation.detailWinnerLabel(selectedMatch) }}</strong>
          <span>{{ selectedMatch.reason }}</span>
        </div>

        <MatchMetricDetail
          v-if="selectedMatchDetailSection"
          :section="selectedMatchDetailSection"
        />

        <Suspense v-else-if="selectedMatchDetailComponent">
          <component
            :is="selectedMatchDetailComponent"
            :match="selectedMatch"
          />
          <template #fallback>
            <p class="stats-loading">
              <LoaderCircle :size="17" /> 正在读取对局复盘…
            </p>
          </template>
        </Suspense>

        <DefaultMatchDetail
          v-else
          :match="selectedMatch"
          :role-label="selectedMatchPresentation.detailPlayerRoleLabel"
        />

        <p class="match-detail-note">
          {{ selectedMatchPresentation.detailNote(selectedMatch) }}
        </p>
      </template>

      <template v-else>
        <span class="modal-icon"><History :size="24" /></span>
        <h2>
          {{ props.gameName
            ? `${props.gameName}${presentation.titleSuffix?.(activeGameMode, activeGameVariant) ?? ''}战绩`
            : '我的全部战绩' }}
        </h2>
        <p>{{ presentation.description }}</p>

        <div
          v-if="presentation.filters?.length && !props.gameMode"
          class="stats-mode-tabs"
          role="group"
          :aria-label="`筛选${props.gameName ?? '游戏'}模式战绩`"
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
          <LoaderCircle :size="24" /> 正在读取战绩…
        </div>
        <template v-else-if="summary">
          <div class="stats-summary-grid">
            <div
              v-for="item in presentation.summaryItems(summary)"
              :key="item.label"
            >
              <strong>{{ item.value }}</strong><span>{{ item.label }}</span>
            </div>
          </div>
          <component
            :is="presentation.summaryComponent"
            v-if="presentation.summaryComponent"
            :summary="summary"
            :mode="activeGameMode"
          />
          <div v-if="presentation.showDrawSummary" class="match-result-summary">
            <span>胜 {{ summary.wins }}</span>
            <span>和 {{ summary.draws }}</span>
            <span>负 {{ summary.losses }}</span>
          </div>

          <div v-if="history.length" class="match-history-list">
            <button v-for="match in history" :key="match.id" type="button" @click="openMatch(match.id)">
              <span :class="['match-outcome', match.outcome]">
                {{ historyPresentation(match).historyOutcome(match) }}
              </span>
              <span class="match-history-copy">
                <strong>{{ historyPresentation(match).historyTitle(match) }}</strong>
                <small>
                  {{ historyPresentation(match).historyMeta(match, formatDate(match.endedAt)) }}
                </small>
              </span>
              <em :class="{ unranked: !match.ranked }">{{ match.ranked ? '计榜' : '测试局' }}</em>
            </button>
          </div>
          <div v-else class="stats-empty">还没有完成的对局</div>
        </template>

        <p v-if="detailLoading" class="stats-loading"><LoaderCircle :size="17" /> 正在打开记录…</p>
      </template>

      <p v-if="error" class="account-error" role="alert">{{ error }}</p>
  </BaseModal>
</template>
