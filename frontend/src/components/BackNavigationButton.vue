<script setup lang="ts">
import { ArrowLeft } from '@lucide/vue'

withDefaults(
  defineProps<{
    label?: string
    disabled?: boolean
  }>(),
  {
    label: '返回',
    disabled: false,
  },
)

defineEmits<{
  click: []
}>()
</script>

<template>
  <button
    type="button"
    class="icon-button back-navigation-button"
    :aria-label="label"
    :disabled="disabled"
    @click="$emit('click')"
  >
    <ArrowLeft :size="21" aria-hidden="true" />
  </button>
</template>
