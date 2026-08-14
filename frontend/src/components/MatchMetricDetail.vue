<script setup lang="ts">
import type { BuiltinGameMatchDetailSection } from '../game-platform/types'

defineProps<{ section: BuiltinGameMatchDetailSection }>()
</script>

<template>
  <div class="match-detail-section">
    <span>{{ section.title }}</span>
    <div class="match-mission-list">
      <div
        v-for="metric in section.metrics"
        :key="metric.label"
        :class="metric.status"
      >
        <strong>{{ metric.label }}</strong>
        <span>{{ metric.value }}</span>
        <small v-if="metric.note">{{ metric.note }}</small>
      </div>
    </div>
  </div>
</template>
