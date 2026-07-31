<script setup lang="ts">
import { ref } from 'vue'
import { Eye, EyeOff } from '@lucide/vue'

withDefaults(
  defineProps<{
    title: string
    subtitle?: string
    hint?: string
  }>(),
  {
    subtitle: '',
    hint: '按住查看，松开隐藏',
  },
)

const emit = defineEmits<{ seen: [] }>()
const pressed = ref(false)
const hasSeen = ref(false)

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
  <button
    type="button"
    class="secret-card"
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
    <div v-if="pressed" class="secret-card__content">
      <Eye :size="22" />
      <strong>{{ title }}</strong>
      <span v-if="subtitle">{{ subtitle }}</span>
      <slot />
    </div>
    <div v-else class="secret-card__cover">
      <EyeOff :size="25" />
      <strong>私密信息</strong>
      <span>{{ hint }}</span>
    </div>
  </button>
</template>
