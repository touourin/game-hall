<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { LoaderCircle, Trophy, X } from '@lucide/vue'
import { loadLeaderboard, type LeaderboardEntry } from '../stats'

const props = defineProps<{ accountId: string; gameKey: string; gameName: string }>()
defineEmits<{ close: [] }>()

const players = ref<LeaderboardEntry[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    players.value = await loadLeaderboard(props.gameKey)
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '读取排行榜失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <section class="modal-card leaderboard-modal" role="dialog" aria-modal="true">
      <button class="modal-close" type="button" aria-label="关闭排行榜" @click="$emit('close')">
        <X :size="20" />
      </button>
      <span class="modal-icon"><Trophy :size="25" /></span>
      <h2>{{ props.gameName }}排行榜</h2>
      <p>{{ props.gameKey === 'reaction' ? '按个人历史最佳三轮平均时间排序，数值越低越快。' : props.gameKey === 'hanoi' ? '按累计通关次数排序，同次数时优先更早完成挑战的玩家。' : '按胜场排序，同胜场时依次比较胜率和有效场次。' }}</p>

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
          <span>
            <strong>{{ player.playerName }}</strong>
            <small v-if="props.gameKey === 'reaction'">{{ player.games }} 次测试 · 总平均 {{ player.averageMs }} ms</small>
            <small v-else-if="props.gameKey === 'hanoi'">{{ player.games }} 次挑战 · {{ player.wins }} 次通关</small>
            <small v-else>
              {{ player.wins }} 胜<span v-if="player.draws"> · {{ player.draws }} 和</span> / {{ player.games }} 场
            </small>
          </span>
          <em>{{ props.gameKey === 'reaction' ? `${player.bestMs} ms` : props.gameKey === 'hanoi' ? `${player.wins} 次` : `${player.winRate}%` }}</em>
        </div>
      </div>
      <div v-else class="stats-empty">还没有符合条件的真人对局</div>
      <p class="leaderboard-note">{{ props.gameKey === 'reaction' ? '排行榜采用完成三轮后的平均反应时间。' : props.gameKey === 'hanoi' ? '不同层数都会累计为一次有效通关，详细步数和时间保存在个人战绩中。' : '含 AI 的测试局不会计入排行榜。' }}</p>
      <p v-if="error" class="account-error" role="alert">{{ error }}</p>
    </section>
  </div>
</template>
