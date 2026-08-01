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
    id: 'avalon',
    name: '翡翠圆桌',
    description: '当前经典深绿与鎏金主题',
    colors: ['#061719', '#123b3a', '#e1bc68'],
  },
  {
    id: 'midnight',
    name: '午夜圣殿',
    description: '沉静蓝黑与银蓝强调色',
    colors: ['#07131f', '#102e42', '#82b9e8'],
  },
  {
    id: 'royal',
    name: '王室秘仪',
    description: '暗紫背景与柔和紫金强调色',
    colors: ['#160f1e', '#35233e', '#d5a8e8'],
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
