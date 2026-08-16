<script setup lang="ts">
import UiIconButton from '../../components/ui/UiIconButton.vue'
import type { PluginIconButtonProps } from '../types'

withDefaults(defineProps<PluginIconButtonProps>(), {
  type: 'button',
  compact: false,
  disabled: false,
})
</script>

<template>
  <UiIconButton
    class="plugin-icon-button"
    :type="type"
    :compact="compact"
    :disabled="disabled"
    :aria-label="label"
  >
    <slot />
  </UiIconButton>
</template>
