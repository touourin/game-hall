<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { LoaderCircle, Trophy, X } from '@lucide/vue'
import { loadLeaderboard, type LeaderboardEntry } from '../stats'

const props = defineProps<{ accountId: string }>()
defineEmits<{ close: [] }>()

const players = ref<LeaderboardEntry[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    players.value = await loadLeaderboard()
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
      <h2>圆桌排行榜</h2>
      <p>按胜场排序，同胜场时依次比较胜率和有效场次。</p>

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
            <strong>{{ player.displayName }}</strong>
            <small>{{ player.wins }} 胜 / {{ player.games }} 场</small>
          </span>
          <em>{{ player.winRate }}%</em>
        </div>
      </div>
      <div v-else class="stats-empty">还没有符合条件的真人对局</div>
      <p class="leaderboard-note">含 AI 的测试局不会计入排行榜。</p>
      <p v-if="error" class="account-error" role="alert">{{ error }}</p>
    </section>
  </div>
</template>
