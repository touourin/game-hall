<script setup lang="ts">
import { Shield, Swords } from '@lucide/vue'
import type { StatsSummary } from '../../stats'

defineProps<{
  summary: StatsSummary
  mode?: string
}>()

function percentage(hits: number | undefined, attempts: number | undefined): string {
  if (!attempts) return '—'
  return `${Math.round(Number(hits ?? 0) / attempts * 100)}%`
}
</script>

<template>
  <div class="alignment-summary">
    <span><Shield :size="15" /> 好人 {{ summary.goodWins }}/{{ summary.goodGames }}</span>
    <span><Swords :size="15" /> 坏人 {{ summary.evilWins }}/{{ summary.evilGames }}</span>
  </div>
  <div v-if="mode === 'court_undercurrent'" class="court-balance-summary">
    <div>
      <strong>{{ percentage(summary.missionRouteGames, summary.games) }}</strong>
      <span>邪恶任务路线</span>
    </div>
    <div>
      <strong>
        {{ percentage(summary.recruitmentHits, summary.recruitmentAttempts) }}
      </strong>
      <span>授刃命中</span>
    </div>
    <div>
      <strong>
        {{ percentage(
          summary.dissentingAssassinationHits,
          summary.dissentingAssassinationAttempts,
        ) }}
      </strong>
      <span>心怀异念之臣刺杀命中</span>
    </div>
  </div>
</template>
