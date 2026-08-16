<script setup lang="ts">
import UiButton from '../../components/ui/UiButton.vue'
import type { PluginButtonProps } from '../types'

withDefaults(defineProps<PluginButtonProps>(), {
  variant: 'secondary',
  type: 'button',
  block: false,
  compact: false,
  disabled: false,
})
</script>

<template>
  <UiButton
    class="plugin-button"
    :variant="variant"
    :type="type"
    :block="block"
    :compact="compact"
    :disabled="disabled"
  >
    <slot />
  </UiButton>
</template>
