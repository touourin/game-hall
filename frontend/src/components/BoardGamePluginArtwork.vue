<script setup lang="ts">
import type { BoardGamePlugin } from '../boardGamePlugins'

defineProps<{
  plugin: BoardGamePlugin
}>()
</script>

<template>
  <span class="board-game-plugin-art" :class="`plugin-tone-${plugin.tone}`" aria-hidden="true">
    <span class="plugin-board-grid">
      <i v-for="cell in 16" :key="cell" />
    </span>
    <span class="plugin-mark">{{ plugin.mark }}</span>
    <span class="plugin-pieces"><i /><i /><i /></span>
  </span>
</template>

<style scoped>
.board-game-plugin-art { --plugin-tone: var(--gold); position: relative; width: 100%; min-height: 150px; display: grid; place-items: center; overflow: hidden; border: 1px solid color-mix(in srgb, var(--plugin-tone) 28%, var(--line)); border-radius: 15px; background: radial-gradient(circle at 50% 18%, color-mix(in srgb, var(--plugin-tone) 20%, transparent), transparent 52%), linear-gradient(145deg, var(--surface-inset), color-mix(in srgb, var(--plugin-tone) 5%, var(--surface-elevated))); color: var(--plugin-tone); }
.board-game-plugin-art::after { position: absolute; inset: 0; background: linear-gradient(135deg, rgba(255,255,255,.045), transparent 42%), repeating-linear-gradient(135deg, transparent 0 11px, rgba(255,255,255,.014) 11px 12px); content: ''; pointer-events: none; }
.plugin-board-grid { position: absolute; inset: 14px; display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid color-mix(in srgb, var(--plugin-tone) 24%, transparent); opacity: .42; transform: perspective(260px) rotateX(16deg) rotateZ(-5deg); }
.plugin-board-grid i { border-right: 1px solid color-mix(in srgb, var(--plugin-tone) 20%, transparent); border-bottom: 1px solid color-mix(in srgb, var(--plugin-tone) 20%, transparent); }
.plugin-board-grid i:nth-child(2n) { background: color-mix(in srgb, var(--plugin-tone) 8%, transparent); }
.plugin-mark { position: relative; z-index: 2; width: 62px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--plugin-tone) 62%, white); border-radius: 18px; color: color-mix(in srgb, var(--plugin-tone) 78%, white); background: color-mix(in srgb, var(--surface-elevated) 76%, transparent); box-shadow: 0 13px 30px rgba(0,0,0,.34), 0 0 0 6px color-mix(in srgb, var(--plugin-tone) 9%, transparent); font-family: "Songti SC", "STSong", serif; font-size: 25px; font-weight: 800; }
.plugin-pieces { position: absolute; z-index: 3; right: 13px; bottom: 11px; display: flex; align-items: flex-end; gap: 5px; }
.plugin-pieces i { width: 12px; height: 18px; border-radius: 50% 50% 35% 35%; background: var(--plugin-tone); box-shadow: 0 4px 9px rgba(0,0,0,.36); }
.plugin-pieces i:nth-child(2) { height: 23px; opacity: .75; }
.plugin-pieces i:nth-child(3) { height: 15px; opacity: .48; }
.plugin-tone-amber { --plugin-tone: #d9ad62; }
.plugin-tone-coral { --plugin-tone: #e7897d; }
.plugin-tone-forest { --plugin-tone: #70c99e; }
.plugin-tone-ocean { --plugin-tone: #77b9df; }
.plugin-tone-violet { --plugin-tone: #ad91df; }
</style>
