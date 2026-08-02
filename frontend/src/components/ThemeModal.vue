<script setup lang="ts">
import { Check, Palette, X } from '@lucide/vue'
import { applyTheme, storedTheme, type ThemeName } from '../theme'
import { ref } from 'vue'

defineEmits<{ close: [] }>()

const selected = ref<ThemeName>(storedTheme())
const themes: Array<{
  id: ThemeName
  name: string
  description: string
  colors: string[]
}> = [
  {
    id: 'emerald',
    name: '墨玉会所',
    description: '黑玉漆面、香槟金与东方纸纹',
    colors: ['#071412', '#173d35', '#d6b76e'],
  },
  {
    id: 'midnight',
    name: '午夜铬光',
    description: '石墨蓝黑、冰蓝与微量紫光',
    colors: ['#070d16', '#172f49', '#75c6e9'],
  },
  {
    id: 'royal',
    name: '象牙棋院',
    description: '暖象牙、墨色与朱砂点睛',
    colors: ['#e9e1d2', '#f7f2e8', '#a54e40'],
  },
]

function chooseTheme(theme: ThemeName) {
  selected.value = theme
  applyTheme(theme)
}
</script>

<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <section class="modal-card theme-modal" role="dialog" aria-modal="true">
      <button class="modal-close" type="button" aria-label="关闭主题" @click="$emit('close')">
        <X :size="20" />
      </button>
      <span class="modal-icon"><Palette :size="25" /></span>
      <h2>界面主题</h2>
      <p>只改变界面氛围；好人、坏人和投票结果的颜色保持一致。</p>

      <div class="theme-list">
        <button
          v-for="theme in themes"
          :key="theme.id"
          type="button"
          :class="{ selected: selected === theme.id }"
          @click="chooseTheme(theme.id)"
        >
          <span class="theme-swatches">
            <i v-for="color in theme.colors" :key="color" :style="{ background: color }" />
          </span>
          <span>
            <strong>{{ theme.name }}</strong>
            <small>{{ theme.description }}</small>
          </span>
          <Check v-if="selected === theme.id" :size="18" />
        </button>
      </div>
    </section>
  </div>
</template>
