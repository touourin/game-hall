<script setup lang="ts">
import {
  difficultyRecordLabel,
  formatMatchDuration,
} from '../../game-platform/recordFormatting'
import type { MatchDetail } from '../../stats'

defineProps<{ match: MatchDetail }>()
</script>

<template>
  <div class="match-detail-section">
    <span>扫雷挑战成绩</span>
    <div class="match-mission-list">
      <div :class="match.winner === 'completed' ? 'success' : 'failed'">
        <strong>
          {{ difficultyRecordLabel(match.details.state?.difficulty) }} ·
          {{ match.details.state?.rows }}×{{ match.details.state?.columns }}
        </strong>
        <span>
          {{ match.winner === 'completed'
            ? formatMatchDuration(match.details.state?.elapsed_ms)
            : '踩中地雷' }}
        </span>
        <small>
          {{ match.details.state?.mine_count }} 雷 · 已翻开
          {{ match.details.state?.revealed_count }} 个安全格
        </small>
      </div>
      <div class="success">
        <strong>本轮标记</strong>
        <span>{{ match.details.state?.flagged_count ?? 0 }} 面旗帜</span>
        <small>首次翻开区域由服务端保证安全</small>
      </div>
    </div>
  </div>
</template>
