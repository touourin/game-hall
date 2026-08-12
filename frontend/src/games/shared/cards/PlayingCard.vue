<script setup lang="ts">
withDefaults(defineProps<{
  rank?: string
  suit?: string
  red?: boolean
  faceDown?: boolean
  empty?: boolean
  selected?: boolean
  wild?: boolean
  joker?: boolean
  interactive?: boolean
  disabled?: boolean
  size?: 'table' | 'mini' | 'compact' | 'bottom' | 'hand'
  ariaLabel?: string
}>(), {
  rank: '',
  suit: '',
  red: false,
  faceDown: false,
  empty: false,
  selected: false,
  wild: false,
  joker: false,
  interactive: false,
  disabled: false,
  size: 'table',
  ariaLabel: '',
})

defineEmits<{ select: [] }>()
</script>

<template>
  <component
    :is="interactive ? 'button' : 'span'"
    class="playing-card"
    :class="[
      `playing-card--${size}`,
      {
        red,
        selected,
        wild,
        joker,
        'card-back': faceDown,
        empty,
      },
    ]"
    :type="interactive ? 'button' : undefined"
    :disabled="interactive ? disabled : undefined"
    :aria-pressed="interactive ? selected : undefined"
    :aria-label="ariaLabel || undefined"
    @click="interactive && $emit('select')"
  >
    <template v-if="faceDown">
      <span class="playing-card__back-mark" aria-hidden="true">♠</span>
    </template>
    <template v-else-if="!empty">
      <b v-if="size === 'bottom'">{{ rank }}{{ suit }}</b>
      <template v-else>
        <b>{{ rank }}</b>
        <span v-if="size === 'hand'" class="playing-card__suit-top">{{ suit }}</span>
        <i aria-hidden="true">{{ suit || rank.slice(0, 1) }}</i>
        <em v-if="wild">癞</em>
      </template>
    </template>
  </component>
</template>

<style scoped>
.playing-card { position: relative; flex: 0 0 auto; width: clamp(42px, 9vw, 64px); aspect-ratio: 5 / 7; min-width: 0; display: grid; align-content: space-between; overflow: hidden; border: 1px solid var(--game-card-border, #d8d4c6); border-radius: 9px; padding: 5px; color: #17211f; background: var(--game-card-face, linear-gradient(145deg, #fffef9, #e2ded4)); box-shadow: 0 7px 16px #0010178a, inset 0 1px 0 rgba(255,255,255,.76); font-family: Georgia, serif; font-style: normal; }
button.playing-card { font: inherit; font-family: Georgia, serif; }
.playing-card b { line-height: 1; font-size: clamp(16px, 3.8vw, 24px); }
.playing-card i { justify-self: end; line-height: 1; font-size: clamp(18px, 4vw, 26px); font-style: normal; }
.playing-card.red { color: #bd2f35; }
.playing-card--mini { width: 32px; border-radius: 5px; padding: 3px; }
.playing-card--mini b { font-size: 12px; }
.playing-card--mini i { font-size: 13px; }
.playing-card--compact { width: 45px; height: 66px; aspect-ratio: auto; padding: 6px; }
.playing-card--compact b { font-size: 16px; }
.playing-card--compact i { justify-self: start; font-size: 17px; }
.playing-card--bottom { width: 30px; height: 38px; aspect-ratio: auto; place-items: center; padding: 2px; }
.playing-card--bottom b { font-size: 12px; }
.playing-card--hand { --card-index: 0; z-index: calc(var(--card-index) + 1); width: clamp(49px, 6.4vw, 65px); height: clamp(94px, 11vw, 121px); aspect-ratio: auto; justify-self: center; display: flex; flex-direction: column; align-items: flex-start; border-radius: 10px; padding: 8px 5px; box-shadow: 0 7px 16px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.7); transform-origin: bottom center; transition: transform .15s ease, border-color .15s, box-shadow .15s, filter .15s; }
.playing-card--hand:not(:disabled) { cursor: pointer; }
.playing-card--hand:disabled { opacity: 1; }
.playing-card--hand:hover:not(:disabled) { transform: translateY(-7px); }
.playing-card--hand.selected { z-index: 80; overflow: visible; border-color: #f1c65c; box-shadow: 0 9px 18px rgba(0,0,0,.55), 0 0 0 3px rgba(241,198,92,.38), 0 0 22px rgba(241,198,92,.35); transform: translateY(-22px) scale(1.035); }
.playing-card--hand b { font-size: clamp(17px, 2vw, 21px); }
.playing-card__suit-top { font-size: clamp(18px, 2.2vw, 24px); line-height: 1; }
.playing-card--hand i { position: absolute; right: 3px; bottom: -5px; color: currentColor; font-size: clamp(28px, 4vw, 46px); opacity: .13; }
.playing-card--hand em { position: absolute; right: 4px; bottom: 4px; color: #a42691; font-style: normal; font-weight: 900; }
.playing-card--hand.joker b { font-size: clamp(13px, 1.7vw, 17px); writing-mode: vertical-rl; letter-spacing: .08em; }
.playing-card--hand.joker i { font-size: 34px; }
.playing-card.wild { box-shadow: 0 0 0 2px #c854bd, 0 5px 13px rgba(0,0,0,.5); }
.card-back { place-items: center; border-color: var(--game-card-back-accent, #d0b06a); color: var(--game-card-back-accent, #e8c978); background: var(--game-card-back, repeating-linear-gradient(45deg, #243d55 0 4px, #172c42 4px 8px)); }
.playing-card__back-mark { font-size: 14px; }
.playing-card.empty { border-style: dashed; border-color: color-mix(in srgb, var(--game-card-back-accent, #e6d392) 28%, transparent); background: rgba(0, 0, 0, .16); box-shadow: none; }
@media (max-width: 600px) {
  .playing-card--table { width: clamp(43px, 12vw, 52px); }
  .playing-card--hand { width: 50px; height: 102px; padding: 7px 4px; }
  .playing-card--hand.selected { transform: translateY(-19px) scale(1.025); }
}
@media (prefers-reduced-motion: reduce) {
  .playing-card--hand { transition: none; }
}
</style>
