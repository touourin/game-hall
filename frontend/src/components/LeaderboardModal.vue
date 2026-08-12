<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { LoaderCircle, Trophy } from '@lucide/vue'
import {
  loadLeaderboard,
  type AvalonStatsVariant,
  type LeaderboardEntry,
} from '../stats'
import AvatarImage from './AvatarImage.vue'
import BaseModal from './ui/BaseModal.vue'

const props = defineProps<{ accountId: string; gameKey: string; gameName: string; gameMode?: string }>()
defineEmits<{ close: [] }>()

const players = ref<LeaderboardEntry[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const activeGameMode = ref<string | undefined>(
  props.gameMode ?? (props.gameKey === 'avalon' ? 'standard' : undefined),
)
const activeAvalonVariant = ref<AvalonStatsVariant | undefined>(
  props.gameKey === 'avalon' && props.gameMode === 'court_undercurrent'
    ? 'classic'
    : undefined,
)

function formatDuration(milliseconds: number | undefined): string {
  if (milliseconds === undefined) return '—'
  const seconds = Math.floor(milliseconds / 1000)
  const tenths = Math.floor(milliseconds % 1000 / 100)
  return `${seconds}.${tenths} 秒`
}

function difficultyLabel(value: string | undefined): string {
  if (value === 'expert') return '高级'
  if (value === 'intermediate') return '中级'
  if (value === 'beginner') return '初级'
  return ''
}

function tetrisModeLabel(value: string | undefined): string {
  if (value?.startsWith('timed_')) return `${Number(value.slice(6)) / 60} 分钟限时`
  return '无限挑战'
}

function avalonModeLabel(): string {
  if (activeGameMode.value !== 'court_undercurrent') return '标准模式'
  return activeAvalonVariant.value === 'shadow_merlin'
    ? '王庭暗流 · 暗影梅林'
    : '王庭暗流 · 无暗影梅林'
}

function selectAvalonStats(
  mode: 'standard' | 'court_undercurrent',
  variant?: AvalonStatsVariant,
) {
  activeGameMode.value = mode
  activeAvalonVariant.value = variant
}

async function loadPlayers() {
  loading.value = true
  error.value = null
  try {
    players.value = await loadLeaderboard(
      props.gameKey,
      activeGameMode.value,
      activeGameMode.value === 'court_undercurrent'
        ? activeAvalonVariant.value
        : undefined,
    )
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '读取排行榜失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadPlayers)
watch([activeGameMode, activeAvalonVariant], loadPlayers)
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
        {{ props.gameName }}{{ props.gameKey === 'avalon' ? ` · ${avalonModeLabel()}` : props.gameKey === 'tetris' ? ` · ${tetrisModeLabel(activeGameMode)}` : difficultyLabel(activeGameMode) }}排行榜
      </h2>
      <p>{{ props.gameKey === 'reaction' ? '按个人历史最佳三轮平均时间排序，数值越低越快。' : props.gameKey === 'schulte' ? '按个人最快完成时间排序，数值越低越快。' : props.gameKey === 'minesweeper' ? '三种难度独立排名，按个人最快通关时间排序。' : props.gameKey === 'tetris' ? '按个人历史最高得分排序，分数越高排名越前。' : props.gameKey === 'hanoi' ? '按累计通关次数排序，同次数时优先更早完成挑战的玩家。' : '按胜场排序，同胜场时依次比较胜率和有效场次。' }}</p>

      <div
        v-if="props.gameKey === 'avalon' && !props.gameMode"
        class="stats-mode-tabs"
        role="group"
        aria-label="筛选阿瓦隆模式排行榜"
      >
        <button
          type="button"
          :class="{ active: activeGameMode === 'standard' }"
          @click="selectAvalonStats('standard')"
        >
          标准模式
        </button>
        <button
          type="button"
          :class="{
            active:
              activeGameMode === 'court_undercurrent' &&
              activeAvalonVariant === 'classic',
          }"
          @click="selectAvalonStats('court_undercurrent', 'classic')"
        >
          暗流 · 无暗影
        </button>
        <button
          type="button"
          :class="{
            active:
              activeGameMode === 'court_undercurrent' &&
              activeAvalonVariant === 'shadow_merlin',
          }"
          @click="selectAvalonStats('court_undercurrent', 'shadow_merlin')"
        >
          暗流 · 暗影梅林
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
            <small v-if="props.gameKey === 'reaction'">{{ player.games }} 次测试 · 总平均 {{ player.averageMs }} ms</small>
            <small v-else-if="props.gameKey === 'schulte'">{{ player.games }} 次挑战 · 平均 {{ formatDuration(player.averageMs) }}</small>
            <small v-else-if="props.gameKey === 'minesweeper'">{{ player.games }} 次通关 · 平均 {{ formatDuration(player.averageMs) }}</small>
            <small v-else-if="props.gameKey === 'hanoi'">{{ player.games }} 次挑战 · {{ player.wins }} 次通关</small>
            <small v-else-if="props.gameKey === 'tetris'">{{ player.games }} 次挑战 · 平均 {{ player.averageScore?.toLocaleString() }} 分</small>
            <small v-else>
              {{ player.wins }} 胜<span v-if="player.draws"> · {{ player.draws }} 和</span> / {{ player.games }} 场
            </small>
          </span>
          <em>{{ props.gameKey === 'reaction' ? `${player.bestMs} ms` : ['schulte', 'minesweeper'].includes(props.gameKey) ? formatDuration(player.bestMs) : props.gameKey === 'tetris' ? `${player.bestScore?.toLocaleString()} 分` : props.gameKey === 'hanoi' ? `${player.wins} 次` : `${player.winRate}%` }}</em>
        </div>
      </div>
      <div v-else class="stats-empty">还没有符合条件的真人对局</div>
      <p class="leaderboard-note">{{ props.gameKey === 'reaction' ? '排行榜采用完成三轮后的平均反应时间。' : props.gameKey === 'schulte' ? '排行榜采用服务端计时，并验证 1–25 的完整点击顺序。' : props.gameKey === 'minesweeper' ? '仅成功清除全部安全方格的服务端计时成绩会进入排行榜。' : props.gameKey === 'tetris' ? '每轮结束后保存最终得分；最高分优先，总平均分用于同分参考。' : props.gameKey === 'hanoi' ? '不同层数都会累计为一次有效通关，详细步数和时间保存在个人战绩中。' : '含 AI 的测试局不会计入排行榜。' }}</p>
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
