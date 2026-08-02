<script setup lang="ts">
import { Check, Images, Maximize2, X } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { ArtworkSkinOption } from './uiTypes'

const props = withDefaults(defineProps<{
  modelValue: string
  options: ArtworkSkinOption[]
  title?: string
  description?: string
  itemName?: string
}>(), {
  title: '我的卡牌画风',
  description: '仅影响你看到的卡牌 · 开局后锁定',
  itemName: '卡牌',
})

const emit = defineEmits<{ 'update:modelValue': [skin: string] }>()
const previewId = ref<string | null>(null)
const preview = computed(() => props.options.find((option) => option.id === previewId.value))

function closePreview() { previewId.value = null }
function usePreview() {
  if (!previewId.value) return
  emit('update:modelValue', previewId.value)
  closePreview()
}
function handleEscape(event: KeyboardEvent) {
  if (event.key === 'Escape') closePreview()
}
onMounted(() => window.addEventListener('keydown', handleEscape))
onBeforeUnmount(() => window.removeEventListener('keydown', handleEscape))
</script>

<template>
  <section class="surface artwork-skin-card" aria-labelledby="artwork-skin-title">
    <div class="artwork-skin-heading">
      <span><Images :size="20" /></span>
      <div><strong id="artwork-skin-title">{{ title }}</strong><small>{{ description }}</small></div>
    </div>
    <div class="artwork-skin-options" role="group" :aria-label="`预览并选择${itemName}画风`">
      <button
        v-for="option in options"
        :key="option.id"
        type="button"
        :data-artwork-skin="option.id"
        :class="{ active: modelValue === option.id }"
        :aria-pressed="modelValue === option.id"
        :aria-label="`查看${option.name}大图预览，${option.tier}画风：${option.description}`"
        @click="previewId = option.id"
      >
        <span class="artwork-skin-preview">
          <img :src="option.preview" :alt="`${option.name}${itemName}画风预览`" loading="lazy" draggable="false" />
          <small>{{ option.tier }}</small>
          <span v-if="modelValue === option.id" class="artwork-skin-check"><Check :size="15" /></span>
          <span class="artwork-skin-expand"><Maximize2 :size="11" />大图</span>
        </span>
        <span class="artwork-skin-copy"><strong>{{ option.name }}</strong><small>{{ option.description }}</small></span>
      </button>
    </div>
  </section>

  <Teleport to="body">
    <div v-if="preview" class="artwork-skin-backdrop" @click.self="closePreview">
      <section class="artwork-skin-modal" role="dialog" aria-modal="true" :aria-labelledby="`artwork-skin-preview-${preview.id}`">
        <header>
          <div><span>{{ preview.tier }}画风</span><h2 :id="`artwork-skin-preview-${preview.id}`">{{ preview.name }}</h2><p>{{ preview.description }} · 确认后才会更换</p></div>
          <button type="button" aria-label="关闭画风大图预览" @click="closePreview"><X :size="20" /></button>
        </header>
        <div class="artwork-skin-gallery">
          <article
            v-for="item in preview.items"
            :key="item.id"
            :data-artwork-treatment="item.framing.treatment"
          >
            <img
              class="artwork-skin-art"
              :class="{ 'preserves-frame': item.framing.preserveFrame }"
              :src="item.artwork"
              :alt="`${preview.name}中的${item.name}`"
              :style="{ '--artwork-scale': item.framing.scale, '--artwork-origin': `${item.framing.originXPercent}% ${item.framing.originYPercent}%` }"
              draggable="false"
            />
            <img
              v-if="item.framing.preserveFrame"
              class="artwork-skin-inner-art"
              :src="item.artwork"
              :style="{ '--artwork-scale': item.framing.scale, '--artwork-origin': `${item.framing.originXPercent}% ${item.framing.originYPercent}%` }"
              alt=""
              aria-hidden="true"
            />
            <div><small>{{ item.group }}</small><strong>{{ item.name }}</strong></div>
          </article>
        </div>
        <footer>
          <span>完整展示 {{ preview.items.length }} 个{{ itemName }}</span>
          <button type="button" :class="{ selected: modelValue === preview.id }" @click="usePreview">
            <Check v-if="modelValue === preview.id" :size="16" />
            {{ modelValue === preview.id ? '当前正在使用' : '使用此画风' }}
          </button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.artwork-skin-card { display: grid; gap: 14px; padding: 16px; }
.artwork-skin-heading { display: flex; align-items: center; gap: 12px; }
.artwork-skin-heading > span { display: grid; flex: 0 0 auto; place-items: center; width: 42px; height: 42px; border: 1px solid color-mix(in srgb, var(--gold) 28%, var(--line)); border-radius: 14px; color: var(--gold); background: color-mix(in srgb, var(--gold) 8%, var(--surface-inset)); }
.artwork-skin-heading > div { display: grid; gap: 4px; }
.artwork-skin-heading strong { font-family: "Songti SC", "STSong", serif; font-size: 14px; }
.artwork-skin-heading small { color: var(--muted); font-size: 10px; }
.artwork-skin-options { display: grid; grid-auto-columns: minmax(154px, 1fr); grid-auto-flow: column; gap: 10px; margin-inline: -4px; padding: 2px 4px 9px; overflow-x: auto; overscroll-behavior-inline: contain; scrollbar-color: color-mix(in srgb, var(--gold) 34%, transparent) transparent; scrollbar-width: thin; scroll-snap-type: inline proximity; }
.artwork-skin-options > button { display: grid; align-content: start; gap: 9px; min-width: 0; overflow: hidden; border: 1px solid var(--line); border-radius: 15px; padding: 6px 6px 10px; color: var(--text); background: rgba(var(--surface-header-rgb), .58); text-align: left; cursor: pointer; scroll-snap-align: start; }
.artwork-skin-options > button.active { border-color: color-mix(in srgb, var(--gold) 55%, var(--line)); background: color-mix(in srgb, var(--gold) 10%, var(--surface-inset)); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--gold) 10%, transparent); }
.artwork-skin-preview { position: relative; display: block; aspect-ratio: 4 / 3; overflow: hidden; border-radius: 10px; background: var(--surface-inset); }
.artwork-skin-preview::after { position: absolute; inset: auto 0 0; height: 42%; background: linear-gradient(transparent, rgba(2, 10, 12, .76)); content: ''; pointer-events: none; }
.artwork-skin-preview img { width: 100%; height: 100%; object-fit: cover; transition: transform 220ms ease; }
.artwork-skin-options button:hover img { transform: scale(1.035); }
.artwork-skin-preview > small, .artwork-skin-check { position: absolute; z-index: 2; top: 7px; display: inline-grid; place-items: center; min-height: 23px; border: 1px solid rgba(255,255,255,.2); color: rgba(255,255,255,.92); background: rgba(2,10,12,.76); box-shadow: 0 3px 12px rgba(0,0,0,.24); backdrop-filter: blur(7px); }
.artwork-skin-preview > small { left: 7px; border-radius: 999px; padding: 0 8px; font-size: 8px; font-weight: 900; }
.artwork-skin-check { right: 7px; width: 23px; border-radius: 50%; color: #ffe297; }
.artwork-skin-expand { position: absolute; z-index: 2; right: 7px; bottom: 7px; display: inline-flex; align-items: center; gap: 3px; border-radius: 999px; padding: 3px 7px; color: rgba(255,255,255,.9); background: rgba(2,10,12,.68); font-size: 8px; font-weight: 850; }
.artwork-skin-copy { display: grid; gap: 3px; min-width: 0; padding-inline: 3px; }
.artwork-skin-copy strong, .artwork-skin-copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.artwork-skin-copy strong { font-family: "Songti SC", "STSong", serif; font-size: 12px; }
.artwork-skin-copy small { color: var(--muted); font-size: 8px; }
.artwork-skin-backdrop { position: fixed; z-index: 80; inset: 0; display: grid; place-items: center; padding: 16px; background: color-mix(in srgb, var(--bg) 88%, transparent); backdrop-filter: blur(12px); }
.artwork-skin-modal { display: grid; grid-template-rows: auto minmax(0, 1fr) auto; width: min(1120px, calc(100vw - 32px)); height: min(94dvh, 940px); min-height: 0; overflow: hidden; border: 1px solid color-mix(in srgb, var(--gold) 30%, var(--line)); border-radius: 24px; color: var(--text); background: var(--modal-surface); box-shadow: var(--shadow); }
.artwork-skin-modal > header, .artwork-skin-modal > footer { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 18px 22px; background: rgba(var(--surface-header-rgb), .92); }
.artwork-skin-modal > header { border-bottom: 1px solid var(--line); }
.artwork-skin-modal > header > div { display: grid; gap: 4px; }
.artwork-skin-modal > header span { width: max-content; border-radius: 999px; padding: 3px 8px; color: var(--gold); background: color-mix(in srgb, var(--gold) 9%, transparent); font-size: 9px; font-weight: 900; }
.artwork-skin-modal h2 { margin: 0; font-family: "Songti SC", "STSong", serif; font-size: clamp(22px, 3vw, 34px); }
.artwork-skin-modal p { margin: 0; color: var(--muted); font-size: 11px; }
.artwork-skin-modal > header button { display: grid; flex: 0 0 auto; place-items: center; width: 40px; height: 40px; border: 1px solid var(--line); border-radius: 50%; color: var(--text-soft); background: var(--surface-inset); cursor: pointer; }
.artwork-skin-gallery { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); grid-auto-rows: max-content; align-content: start; gap: 14px; min-height: 0; padding: 20px 22px 26px; overflow-y: auto; }
.artwork-skin-gallery article { position: relative; min-width: 0; overflow: hidden; aspect-ratio: 2 / 3; border: 1px solid var(--line); border-radius: 17px; background: #031010; box-shadow: 0 12px 27px rgba(0,0,0,.28); }
.artwork-skin-art, .artwork-skin-inner-art { width: 100%; height: 100%; object-fit: cover; }
.artwork-skin-art { transform: scale(var(--artwork-scale, 1)); transform-origin: var(--artwork-origin, 50% 50%); }
.artwork-skin-art.preserves-frame { transform: none; }
.artwork-skin-inner-art { position: absolute; z-index: 1; inset: 0; pointer-events: none; transform: scale(var(--artwork-scale, 1)); transform-origin: var(--artwork-origin, 50% 50%); -webkit-mask-image: radial-gradient(ellipse 38% 42% at 50% 42%, #000 0 75%, rgba(0,0,0,.76) 84%, transparent 100%); mask-image: radial-gradient(ellipse 38% 42% at 50% 42%, #000 0 75%, rgba(0,0,0,.76) 84%, transparent 100%); }
.artwork-skin-gallery article > div { position: absolute; z-index: 2; inset: auto 0 0; display: grid; justify-items: center; gap: 3px; min-height: 30%; align-content: end; padding: 34px 9px 13px; color: #f3f2e8; background: linear-gradient(transparent, rgba(2,9,10,.93) 50%, #02090a); text-align: center; }
.artwork-skin-gallery article[data-artwork-treatment="codex-ink-wash"] > div { min-height: 44%; padding-top: 58px; background: linear-gradient(180deg, transparent 0%, rgba(7,18,27,.72) 14%, #07121b 28%, #02090a 100%); }
.artwork-skin-gallery article small { color: #b9ccc7; font-size: 8px; font-weight: 800; letter-spacing: .1em; }
.artwork-skin-gallery article strong { font-family: "Songti SC", "STSong", serif; font-size: clamp(15px, 1.8vw, 22px); }
.artwork-skin-modal > footer { border-top: 1px solid var(--line); }
.artwork-skin-modal > footer > span { color: var(--muted); font-size: 10px; }
.artwork-skin-modal > footer button { display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-width: 146px; min-height: 43px; border: 0; border-radius: 12px; padding: 0 18px; color: var(--accent-contrast); background: linear-gradient(135deg, var(--accent-highlight), var(--gold)); font-size: 12px; font-weight: 900; cursor: pointer; }
.artwork-skin-modal > footer button.selected { border: 1px solid color-mix(in srgb, var(--gold) 30%, var(--line)); color: var(--gold); background: color-mix(in srgb, var(--gold) 9%, var(--surface-inset)); }
@media (min-width: 820px) { .artwork-skin-options { grid-auto-flow: initial; grid-template-columns: repeat(5, minmax(0, 1fr)); } }
@media (max-width: 720px) { .artwork-skin-backdrop { align-items: end; padding: 8px; } .artwork-skin-modal { width: 100%; height: calc(100dvh - 8px); border-radius: 20px 20px 0 0; } .artwork-skin-modal > header, .artwork-skin-modal > footer { padding: 14px; } .artwork-skin-gallery { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; padding: 12px 12px 20px; } }
@media (max-width: 430px) { .artwork-skin-card { padding-inline: 13px; } .artwork-skin-options { grid-auto-columns: minmax(148px, 46vw); } .artwork-skin-modal > footer { align-items: stretch; flex-direction: column; } .artwork-skin-modal > footer button { width: 100%; } }
</style>
