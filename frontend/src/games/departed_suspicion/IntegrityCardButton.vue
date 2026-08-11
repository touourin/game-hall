<script setup lang="ts">
import { computed, ref } from 'vue'
import type { IntegrityView } from './types'

const props = defineProps<{
  card: IntegrityView
  ownerName: string
  finished: boolean
}>()

const pressed = ref(false)
const isPublic = computed(() => props.finished || props.card.revealed)
const canRevealPrivately = computed(() => (
  !isPublic.value
  && props.card.kind !== null
  && (props.card.knowledge === 'own' || props.card.knowledge === 'known')
))
const isVisible = computed(() => isPublic.value || (canRevealPrivately.value && pressed.value))
const classes = computed(() => [
  isVisible.value && props.card.kind ? `kind-${props.card.kind}` : 'kind-hidden',
  isPublic.value ? 'revealed' : 'face-down',
  `knowledge-${props.card.knowledge}`,
  canRevealPrivately.value ? 'private-viewable' : '',
  isVisible.value && !isPublic.value ? 'private-revealed' : '',
])
const status = computed(() => {
  if (props.card.wounded && isPublic.value) return '受伤'
  if (isPublic.value) return '公开'
  if (isVisible.value) return '仅你可见'
  if (props.card.knowledge === 'known') return '已掌握 · 按住查看'
  if (props.card.knowledge === 'own') return '按住查看'
  return '暗置'
})
const ariaLabel = computed(() => {
  const position = `${props.ownerName}第${props.card.index + 1}张底细`
  if (!canRevealPrivately.value) return position
  return props.card.knowledge === 'known'
    ? `按住查看已掌握的${position}`
    : `按住查看自己的第${props.card.index + 1}张底细`
})

function reveal() {
  if (canRevealPrivately.value) pressed.value = true
}

function hide() {
  pressed.value = false
}
</script>

<template>
  <button
    type="button"
    class="integrity-card"
    :class="classes"
    :disabled="!canRevealPrivately"
    :aria-label="ariaLabel"
    @pointerdown.prevent="reveal"
    @pointerup.prevent="hide"
    @pointercancel="hide"
    @pointerleave="hide"
    @keydown.space.prevent="reveal"
    @keyup.space.prevent="hide"
    @keydown.enter.prevent="reveal"
    @keyup.enter.prevent="hide"
    @contextmenu.prevent
  >
    <span>{{ isVisible && card.kind ? card.label : '?' }}</span>
    <small>{{ status }}</small>
  </button>
</template>

<style scoped>
.integrity-card { position: relative; min-width: 0; min-height: 94px; display: grid; place-items: center; align-content: center; gap: 8px; border: 1px solid var(--line); border-radius: 10px; color: var(--text); background: linear-gradient(145deg, var(--surface-elevated), var(--surface-inset)); overflow: hidden; opacity: 1; touch-action: none; -webkit-touch-callout: none; -webkit-user-select: none; user-select: none; }
.integrity-card::before { position: absolute; inset: 4px; border: 1px solid currentColor; border-radius: 7px; content: ''; opacity: .16; }
.integrity-card span { position: relative; z-index: 1; font-family: "Songti SC", serif; font-size: 18px; font-weight: 900; }
.integrity-card small { position: relative; z-index: 1; color: var(--muted); font-size: 8px; }
.integrity-card.kind-honest { color: #8cc8d8; }
.integrity-card.kind-crooked { color: #de8a82; }
.integrity-card.kind-agent { color: #ddbc72; background: radial-gradient(circle at 50% 20%, rgba(221,188,114,.13), transparent 55%), var(--surface-inset); }
.integrity-card.kind-kingpin { color: #d56d66; background: radial-gradient(circle at 50% 20%, rgba(213,109,102,.14), transparent 55%), var(--surface-inset); }
.integrity-card.kind-hidden { color: #777d7a; background: repeating-linear-gradient(135deg, rgba(255,255,255,.025) 0 7px, transparent 7px 14px), var(--surface-inset); }
.integrity-card.knowledge-known { border-style: dashed; border-color: color-mix(in srgb, var(--case-gold) 58%, var(--line)); }
.integrity-card.private-viewable { cursor: pointer; }
.integrity-card.private-revealed { box-shadow: inset 0 0 0 2px color-mix(in srgb, currentColor 42%, transparent); }
.integrity-card.revealed { box-shadow: inset 0 -3px 0 color-mix(in srgb, currentColor 40%, transparent); }
@media (max-width: 760px) {
  .integrity-card { min-height: 58px; gap: 4px; border-radius: 7px; }
  .integrity-card span { font-size: 12px; }
  .integrity-card small { font-size: 7px; }
}
</style>
