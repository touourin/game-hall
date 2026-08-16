<script setup lang="ts">
import { computed, ref } from 'vue'
import { Check, ChevronRight, LayoutPanelTop, PanelsTopLeft, X } from '@lucide/vue'
import {
  GAME_SKINS,
  gameSkinCssVariables,
  type GameSkinId,
  type GameSkinKind,
} from '../gameSkins'
import UiIconButton from './ui/UiIconButton.vue'

const props = defineProps<{
  modelValue: GameSkinId
  kind: GameSkinKind
}>()

const emit = defineEmits<{
  'update:modelValue': [skin: GameSkinId]
}>()

const mobileOpen = ref(false)
const selectedSkin = computed(() => (
  GAME_SKINS.find((skin) => skin.id === props.modelValue) ?? GAME_SKINS[0]!
))

function selectSkin(skin: GameSkinId) {
  emit('update:modelValue', skin)
  mobileOpen.value = false
}
</script>

<template>
  <section class="surface game-skin-card" aria-labelledby="game-skin-title">
    <div class="game-skin-heading">
      <span class="game-skin-icon">
        <PanelsTopLeft v-if="props.kind === 'board'" :size="20" />
        <LayoutPanelTop v-else :size="20" />
      </span>
      <div>
        <strong id="game-skin-title">我的{{ props.kind === 'board' ? '棋盘' : '扑克' }}画风</strong>
        <small>仅影响你看到的{{ props.kind === 'board' ? '棋盘和棋子' : '牌桌和扑克' }} · 开局后保持</small>
      </div>
    </div>

    <button
      type="button"
      class="game-skin-mobile-trigger"
      aria-label="更换本局画风"
      @click="mobileOpen = true"
    >
      <span>
        <small>当前画风</small>
        <strong>{{ selectedSkin.name }}</strong>
      </span>
      <span>{{ selectedSkin.tier }} <ChevronRight :size="16" /></span>
    </button>

    <button
      v-if="mobileOpen"
      type="button"
      class="game-skin-mobile-backdrop"
      aria-label="关闭画风选择"
      @click="mobileOpen = false"
    />

    <div
      class="game-skin-options"
      :class="{ 'is-mobile-open': mobileOpen }"
      role="group"
      :aria-label="`预览并选择本局${props.kind === 'board' ? '棋盘' : '扑克'}画风`"
    >
      <header class="game-skin-mobile-sheet-header">
        <span><small>LOCAL APPEARANCE</small><strong>选择本局画风</strong></span>
        <UiIconButton class="adaptive-touch-target" aria-label="关闭画风选择" @click="mobileOpen = false"><X :size="19" /></UiIconButton>
      </header>
      <button
        v-for="skin in GAME_SKINS"
        :key="skin.id"
        type="button"
        :data-game-skin-option="skin.id"
        :class="{ active: modelValue === skin.id }"
        :aria-pressed="modelValue === skin.id"
        :aria-label="`${skin.name}，${skin.tier}皮肤：${skin.description}`"
        @click="selectSkin(skin.id)"
      >
        <span class="game-skin-preview" :style="gameSkinCssVariables(skin.id)">
          <span class="preview-board" aria-hidden="true">
            <i class="preview-stone black" />
            <i class="preview-stone white" />
          </span>
          <span class="preview-table" aria-hidden="true">
            <i class="preview-card card-one">A</i>
            <i class="preview-card card-two">K</i>
            <i class="preview-card card-back" />
          </span>
          <small class="game-skin-tier" :data-tier="skin.tier">{{ skin.tier }}</small>
          <span v-if="modelValue === skin.id" class="game-skin-check" aria-hidden="true">
            <Check :size="15" />
          </span>
        </span>
        <span class="game-skin-copy">
          <strong>{{ skin.name }}</strong>
          <small>{{ skin.description }}</small>
        </span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.game-skin-card { display: grid; gap: 14px; padding: 16px; }
.game-skin-heading { display: flex; align-items: center; gap: 12px; }
.game-skin-heading > div { display: grid; gap: 4px; }
.game-skin-heading strong { font-family: "Songti SC", "STSong", serif; font-size: 14px; }
.game-skin-heading small { color: var(--muted); font-size: 10px; }
.game-skin-icon { display: grid; flex: 0 0 auto; place-items: center; width: 42px; height: 42px; border: 1px solid color-mix(in srgb, var(--accent) 18%, transparent); border-radius: 14px; color: var(--accent); background: color-mix(in srgb, var(--accent) 8%, transparent); }
.game-skin-mobile-trigger, .game-skin-mobile-sheet-header, .game-skin-mobile-backdrop { display: none; }
.game-skin-options { display: grid; grid-auto-columns: minmax(154px, 1fr); grid-auto-flow: column; gap: 10px; margin-inline: -4px; padding: 2px 4px 9px; overflow-x: auto; overscroll-behavior-inline: contain; scrollbar-color: color-mix(in srgb, var(--accent) 34%, transparent) transparent; scrollbar-width: thin; scroll-snap-type: inline proximity; }
.game-skin-options > button { display: grid; align-content: start; gap: 9px; min-width: 0; border: 1px solid var(--line); border-radius: 15px; padding: 6px 6px 10px; color: var(--text); background: rgba(var(--surface-header-rgb),.58); text-align: left; cursor: pointer; overflow: hidden; scroll-snap-align: start; transition: border-color 160ms ease, background 160ms ease, transform 160ms ease; }
.game-skin-options > button.active { border-color: color-mix(in srgb, var(--accent) 52%, transparent); background: color-mix(in srgb, var(--accent) 11%, transparent); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--accent) 8%, transparent); }
.game-skin-options > button:active { transform: scale(.985); }
.game-skin-preview { position: relative; display: grid; grid-template-columns: 1fr 1fr; gap: 5px; aspect-ratio: 4 / 3; padding: 18px 8px 8px; border-radius: 10px; background: #071512; overflow: hidden; }
.preview-board { position: relative; border: 3px solid var(--game-board-frame); border-radius: 5px; background-color: var(--game-board-surface); background-image: linear-gradient(var(--game-board-line) 1px, transparent 1px), linear-gradient(90deg, var(--game-board-line) 1px, transparent 1px), var(--game-board-texture); background-position: center; background-size: 16% 16%, 16% 16%, auto; box-shadow: inset 0 0 0 1px var(--game-board-highlight); }
.preview-stone { position: absolute; width: 22%; aspect-ratio: 1; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,.5); }
.preview-stone.black { top: 27%; left: 29%; background: var(--game-black-stone); }
.preview-stone.white { right: 18%; bottom: 19%; border: 1px solid var(--game-white-stone-border); background: var(--game-white-stone); }
.preview-table { position: relative; border: 3px solid var(--game-felt-border); border-radius: 50% / 38%; background: var(--game-felt-surface); box-shadow: inset 0 0 0 1px var(--game-felt-highlight); }
.preview-card { position: absolute; display: grid; place-items: center; width: 31%; aspect-ratio: .7; border: 1px solid var(--game-card-border); border-radius: 3px; color: #8d2525; background: var(--game-card-face); font-size: clamp(7px, 1vw, 11px); font-style: normal; font-weight: 900; box-shadow: 0 2px 5px rgba(0,0,0,.34); }
.preview-card.card-one { top: 24%; left: 18%; transform: rotate(-9deg); }
.preview-card.card-two { top: 19%; left: 39%; color: #1a2530; transform: rotate(6deg); }
.preview-card.card-back { right: 10%; bottom: 11%; color: var(--game-card-back-accent); background: var(--game-card-back); transform: rotate(14deg); }
.game-skin-tier, .game-skin-check { position: absolute; z-index: 2; top: 6px; display: inline-grid; place-items: center; min-height: 22px; border: 1px solid rgba(255,255,255,.2); color: rgba(255,255,255,.92); background: rgba(2,10,12,.76); box-shadow: 0 3px 12px rgba(0,0,0,.24); backdrop-filter: blur(7px); }
.game-skin-tier { left: 7px; border-radius: 999px; padding: 0 8px; font-size: 8px; font-weight: 900; letter-spacing: .08em; }
.game-skin-tier[data-tier="高级"] { border-color: rgba(255,226,151,.62); color: #ffe297; background: rgba(83,55,9,.82); }
.game-skin-check { right: 7px; width: 23px; border-color: color-mix(in srgb, var(--accent) 58%, transparent); border-radius: 50%; color: var(--primary-text); background: var(--primary-end); }
.game-skin-copy { display: grid; gap: 3px; min-width: 0; padding-inline: 3px; }
.game-skin-copy strong, .game-skin-copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.game-skin-copy strong { font-family: "Songti SC", "STSong", serif; font-size: 12px; }
.game-skin-copy small { color: var(--muted); font-size: 8px; }

@media (min-width: 820px) {
  .game-skin-options { grid-auto-flow: initial; grid-template-columns: repeat(5, minmax(0, 1fr)); }
}

@media (max-width: 430px) {
  .game-skin-card { padding-inline: 13px; }
}

@media (max-width: 720px) {
  .game-skin-card { gap: 12px; }
  .game-skin-mobile-trigger { display: flex; align-items: center; justify-content: space-between; gap: 12px; width: 100%; min-height: 60px; border: 1px solid color-mix(in srgb, var(--accent) 28%, var(--line)); border-radius: 13px; padding: 10px 12px; color: var(--text); background: color-mix(in srgb, var(--accent) 7%, var(--surface-inset)); text-align: left; }
  .game-skin-mobile-trigger > span { display: flex; align-items: center; gap: 7px; }
  .game-skin-mobile-trigger > span:first-child { display: grid; gap: 2px; }
  .game-skin-mobile-trigger small { color: var(--muted); font-size: 9px; }
  .game-skin-mobile-trigger strong { font-family: "Songti SC", "STSong", serif; font-size: 14px; }
  .game-skin-mobile-trigger > span:last-child { color: var(--accent); font-size: 10px; font-weight: 850; }
  .game-skin-options { display: none; }
  .game-skin-mobile-backdrop { position: fixed; z-index: 90; inset: 0; display: block; width: 100%; border: 0; background: color-mix(in srgb, var(--bg) 76%, transparent); backdrop-filter: blur(8px); }
  .game-skin-options.is-mobile-open { position: fixed; z-index: 91; right: 8px; bottom: 0; left: 8px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); grid-auto-flow: row; grid-auto-columns: auto; gap: 9px; max-height: min(82dvh, 720px); margin: 0; border: 1px solid color-mix(in srgb, var(--accent) 30%, var(--line)); border-bottom: 0; border-radius: 22px 22px 0 0; padding: 12px 12px calc(16px + env(safe-area-inset-bottom)); overflow-x: hidden; overflow-y: auto; background: var(--material-pattern), var(--modal-surface); box-shadow: 0 -20px 70px rgba(0,0,0,.42); scroll-snap-type: none; }
  .game-skin-mobile-sheet-header { position: sticky; z-index: 3; top: -12px; grid-column: 1 / -1; display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: -12px -12px 3px; border-bottom: 1px solid var(--line); padding: 14px; background: color-mix(in srgb, var(--modal-surface) 94%, transparent); backdrop-filter: blur(14px); }
  .game-skin-mobile-sheet-header > span { display: grid; gap: 2px; }
  .game-skin-mobile-sheet-header small { color: var(--accent); font-size: 8px; font-weight: 900; letter-spacing: .12em; }
  .game-skin-mobile-sheet-header strong { font-family: "Songti SC", "STSong", serif; font-size: 17px; }
  .game-skin-options.is-mobile-open > button { scroll-snap-align: none; }
}
</style>
