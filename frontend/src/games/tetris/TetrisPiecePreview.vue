<script setup lang="ts">
import { computed } from 'vue'
import { previewCells, type PieceType } from './tetrisEngine'

const props = defineProps<{ piece: PieceType | null }>()
const occupiedCells = computed(() => props.piece ? previewCells(props.piece) : new Set<string>())
</script>

<template>
  <span class="mini-grid" :class="{ empty: !piece }">
    <i
      v-for="cell in 16"
      :key="cell"
      :class="piece && occupiedCells.has(`${(cell - 1) % 4}:${Math.floor((cell - 1) / 4)}`) ? `piece-${piece}` : ''"
    />
  </span>
</template>

<style scoped>
.mini-grid { width: 100%; max-width: var(--tetris-preview-size, 88px); aspect-ratio: 1; margin: 0 auto; display: grid; grid-template-columns: repeat(4, 1fr); padding: 2px; }
.mini-grid i { min-width: 0; aspect-ratio: 1; border: 1px solid transparent; }
.mini-grid i[class*="piece-"] { border-color: color-mix(in srgb, var(--cell-color) 72%, white); border-radius: 2px; background: var(--cell-color); box-shadow: inset 1px 1px 0 #ffffff55; }
.piece-I { --cell-color: var(--piece-I); }.piece-J { --cell-color: var(--piece-J); }.piece-L { --cell-color: var(--piece-L); }.piece-O { --cell-color: var(--piece-O); }.piece-S { --cell-color: var(--piece-S); }.piece-T { --cell-color: var(--piece-T); }.piece-Z { --cell-color: var(--piece-Z); }
</style>
