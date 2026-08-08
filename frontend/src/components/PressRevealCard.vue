<script setup lang="ts">
import { computed, ref } from 'vue'
import { Eye, EyeOff, Lock } from '@lucide/vue'
import type { RevealArtworkFraming } from './uiTypes'

const props = withDefaults(
  defineProps<{
    title: string
    subtitle?: string
    hint?: string
    artwork?: string | null
    artworkLabel?: string
    artworkFraming?: RevealArtworkFraming
  }>(),
  {
    subtitle: '',
    hint: '按住查看，松开隐藏',
    artwork: null,
    artworkLabel: '',
    artworkFraming: () => ({
      scale: 1,
      originXPercent: 50,
      originYPercent: 50,
    }),
  },
)

const emit = defineEmits<{ seen: [] }>()
const pressed = ref(false)
const hasSeen = ref(false)
const artworkStyle = computed(() => ({
  backgroundImage: props.artwork ? `url(${JSON.stringify(props.artwork)})` : undefined,
}))

function reveal() {
  pressed.value = true
  if (!hasSeen.value) {
    hasSeen.value = true
    emit('seen')
  }
}

function hide() {
  pressed.value = false
}
</script>

<template>
  <div class="press-reveal-shell" :class="{ illustrated: Boolean(artwork) }">
    <div v-if="artwork && artworkLabel" class="press-reveal-art-label">
      <Lock :size="13" />
      <span>本局画风</span>
      <strong>{{ artworkLabel }}</strong>
    </div>

    <button
      type="button"
      class="press-reveal-card"
      :class="{ illustrated: Boolean(artwork) }"
      @pointerdown.prevent="reveal"
      @pointerup.prevent="hide"
      @pointercancel="hide"
      @pointerleave="hide"
      @keydown.space.prevent="reveal"
      @keyup.space.prevent="hide"
      @keydown.enter.prevent="reveal"
      @keyup.enter.prevent="hide"
      @contextmenu.prevent
      @dragstart.prevent
      @selectstart.prevent
    >
      <template v-if="pressed">
        <span
          v-if="artwork"
          class="press-reveal-art"
          :style="artworkStyle"
          aria-hidden="true"
        />
        <div class="press-reveal-content" :class="{ illustrated: Boolean(artwork) }">
          <Eye :size="22" />
          <strong>{{ title }}</strong>
          <span v-if="subtitle">{{ subtitle }}</span>
          <slot />
        </div>
      </template>
      <div v-else class="press-reveal-cover">
        <EyeOff :size="25" />
        <strong>私密信息</strong>
        <span>{{ hint }}</span>
      </div>
    </button>
  </div>
</template>

<style scoped>
.press-reveal-shell { display: grid; gap: 10px; -webkit-touch-callout: none; }
.press-reveal-shell.illustrated { width: min(100%, 400px); margin-inline: auto; }
.press-reveal-art-label { display: inline-flex; align-items: center; justify-self: end; gap: 6px; border: 1px solid color-mix(in srgb, var(--gold) 28%, var(--line)); border-radius: 999px; padding: 6px 9px; color: var(--muted); background: color-mix(in srgb, var(--gold) 7%, var(--surface-inset)); font-size: 9px; font-weight: 850; }
.press-reveal-art-label svg, .press-reveal-art-label strong { color: var(--gold); }
.press-reveal-card { position: relative; display: grid; width: 100%; min-height: 300px; overflow: hidden; border: 1px solid color-mix(in srgb, var(--gold) 36%, var(--line)); border-radius: 26px; padding: 24px; color: var(--text); background: radial-gradient(circle at 50% 15%, color-mix(in srgb, var(--gold) 14%, transparent), transparent 34%), var(--surface-elevated); box-shadow: var(--shadow-card); cursor: pointer; touch-action: none; -webkit-touch-callout: none; -webkit-user-select: none; user-select: none; }
.press-reveal-card.illustrated { aspect-ratio: 2 / 3; min-height: 0; border: 0; padding: 0; color: #f5f3e9; background: #071412; box-shadow: none; isolation: isolate; }
.press-reveal-card::before, .press-reveal-card::after { position: absolute; width: 110px; height: 110px; border: 1px solid color-mix(in srgb, var(--gold) 18%, transparent); border-radius: 50%; content: ''; }
.press-reveal-card::before { top: -54px; left: -54px; }
.press-reveal-card::after { right: -54px; bottom: -54px; }
.press-reveal-card.illustrated::before, .press-reveal-card.illustrated::after { display: none; }
.press-reveal-cover, .press-reveal-content { position: relative; z-index: 2; display: grid; place-items: center; align-content: center; gap: 10px; text-align: center; }
.press-reveal-cover svg, .press-reveal-content > svg { color: var(--gold); }
.press-reveal-cover strong { font-family: "Songti SC", serif; font-size: 24px; }
.press-reveal-cover span { color: var(--muted); font-size: 11px; }
.press-reveal-content > strong { font-family: "Songti SC", serif; font-size: 34px; }
.press-reveal-content > span { color: var(--text-soft); font-size: 12px; font-weight: 700; }
.press-reveal-art { position: absolute; z-index: 0; inset: 0; width: 100%; height: 100%; background-position: center; background-repeat: no-repeat; background-size: contain; pointer-events: none; }
.press-reveal-content.illustrated { align-content: end; min-height: inherit; padding: 58% 22px 23px; }
.press-reveal-content.illustrated > svg { filter: drop-shadow(0 2px 7px rgba(0, 0, 0, .75)); }
.press-reveal-content.illustrated > strong, .press-reveal-content.illustrated > span, .press-reveal-content.illustrated :deep(.secret-description), .press-reveal-content.illustrated :deep(.muted-secret) { text-shadow: 0 2px 9px rgba(0, 0, 0, .9); }
.press-reveal-content.illustrated :deep(.secret-description) { color: #d2e1da; }
.press-reveal-content.illustrated :deep(.knowledge-list span) { border-color: rgba(255, 255, 255, .18); color: #fff; background: rgba(2, 10, 12, .66); backdrop-filter: blur(7px); }
.press-reveal-content.illustrated :deep(.muted-secret) { color: rgba(255, 255, 255, .68); }
@media (max-width: 430px) { .press-reveal-content.illustrated { padding-right: 16px; padding-bottom: 18px; padding-left: 16px; } }
</style>
