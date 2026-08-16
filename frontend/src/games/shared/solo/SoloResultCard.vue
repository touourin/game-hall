<script setup lang="ts">
import { RotateCcw } from '@lucide/vue'
import type { GameMetricItem } from '../../../components/uiTypes'
import UiButton from '../../../components/ui/UiButton.vue'
import SoloMetricGrid from './SoloMetricGrid.vue'

withDefaults(defineProps<{
  eyebrow: string
  title: string
  description?: string | null
  score?: string | number | null
  scoreUnit?: string
  metrics?: GameMetricItem[]
  restartLabel?: string
  canRestart?: boolean
  busy?: boolean
  tone?: 'success' | 'danger' | 'neutral'
}>(), {
  description: '',
  score: null,
  scoreUnit: '',
  metrics: () => [],
  restartLabel: '再挑战一次',
  canRestart: false,
  busy: false,
  tone: 'success',
})

defineEmits<{ restart: [] }>()
</script>

<template>
  <section class="surface solo-result-card" :class="[`tone-${tone}`, { 'has-score': score !== null }]">
    <span class="solo-result-eyebrow"><slot name="icon" />{{ eyebrow }}</span>
    <strong v-if="score !== null" class="solo-result-score">{{ score }} <small v-if="scoreUnit">{{ scoreUnit }}</small></strong>
    <h2>{{ title }}</h2>
    <p v-if="description">{{ description }}</p>
    <SoloMetricGrid v-if="metrics.length" class="solo-result-metrics" :items="metrics" value-first />
    <slot name="note" />
    <UiButton
      v-if="canRestart"
      class="solo-result-restart"
      variant="primary"
      :disabled="busy"
      @click="$emit('restart')"
    >
      <RotateCcw :size="18" />{{ restartLabel }}
    </UiButton>
  </section>
</template>

<style scoped>
.solo-result-card { padding: clamp(22px, 4vw, 30px); display: grid; justify-items: center; gap: 8px; border-color: color-mix(in srgb, var(--result-tone, var(--green)) 24%, var(--line)); background: radial-gradient(circle at 50% 0, color-mix(in srgb, var(--result-tone, var(--green)) 7%, transparent), transparent 46%), var(--surface-glass); box-shadow: var(--shadow-raised), inset 0 1px 0 var(--metal-edge); text-align: center; }
.solo-result-card.tone-danger { --result-tone: var(--red); }
.solo-result-card.tone-neutral { --result-tone: var(--accent); }
.solo-result-eyebrow { display: inline-flex; align-items: center; gap: 7px; color: var(--result-tone, var(--green)); font-size: 11px; font-weight: 900; letter-spacing: .05em; }
.solo-result-score { color: var(--text); font-size: clamp(44px, 10vw, 68px); font-weight: 760; letter-spacing: -.05em; line-height: 1; }
.solo-result-score small { color: var(--accent); font-size: .3em; }
.solo-result-card h2 { margin: 3px 0 0; font-size: clamp(30px, 6vw, 46px); }
.solo-result-card.has-score h2 { margin-top: 0; color: var(--muted); font-family: inherit; font-size: 12px; font-weight: 750; }
.solo-result-card > p { margin: 0; color: var(--muted); font-size: 11px; line-height: 1.6; }
.solo-result-metrics { width: min(100%, 520px); margin: 8px 0 2px; }
.solo-result-restart { margin-top: 8px; }
@media (max-width: 520px) {
  .solo-result-card { padding: 20px 14px; }
  .solo-result-card h2 { font-size: clamp(28px, 9vw, 39px); }
}
</style>
