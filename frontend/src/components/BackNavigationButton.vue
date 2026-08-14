<script setup lang="ts">
import { ArrowLeft } from '@lucide/vue'
import UiIconButton from './ui/UiIconButton.vue'

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
  <UiIconButton
    class="back-navigation-button"
    :aria-label="label"
    :disabled="disabled"
    @click="$emit('click')"
  >
    <ArrowLeft :size="21" aria-hidden="true" />
  </UiIconButton>
</template>
