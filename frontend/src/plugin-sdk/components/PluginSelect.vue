<script setup lang="ts">
import { computed, useAttrs, useId } from 'vue'
import PluginFieldShell from './PluginFieldShell.vue'
import type { PluginSelectProps } from '../types'

defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<PluginSelectProps>(), {
  id: '',
  name: '',
  placeholder: '',
  description: '',
  error: '',
  disabled: false,
  required: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  blur: [event: FocusEvent]
}>()

const attrs = useAttrs()
const generatedId = `plugin-select-${useId()}`
const inputId = computed(() => props.id || generatedId)
</script>

<template>
  <PluginFieldShell
    :input-id="inputId"
    :label="label"
    :description="description"
    :error="error"
    :required="required"
  >
    <template #default="{ describedBy }">
      <select
        v-bind="attrs"
        :id="inputId"
        class="plugin-field-control plugin-select"
        :value="modelValue"
        :name="name || undefined"
        :disabled="disabled"
        :required="required"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describedBy"
        @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
        @blur="emit('blur', $event)"
      >
        <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
        <option
          v-for="option in options"
          :key="option.value"
          :value="option.value"
          :disabled="option.disabled"
        >
          {{ option.label }}
        </option>
      </select>
    </template>
  </PluginFieldShell>
</template>

<style scoped>
.plugin-select { cursor: pointer; }
</style>
