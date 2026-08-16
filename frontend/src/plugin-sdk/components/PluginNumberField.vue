<script setup lang="ts">
import { computed, useAttrs, useId } from 'vue'
import PluginFieldShell from './PluginFieldShell.vue'
import type { PluginNumberFieldProps } from '../types'

defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<PluginNumberFieldProps>(), {
  id: '',
  name: '',
  min: undefined,
  max: undefined,
  step: 1,
  inputmode: 'decimal',
  placeholder: '',
  description: '',
  error: '',
  disabled: false,
  required: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
  blur: [event: FocusEvent]
}>()

const attrs = useAttrs()
const generatedId = `plugin-number-field-${useId()}`
const inputId = computed(() => props.id || generatedId)

function updateValue(event: Event) {
  const input = event.target as HTMLInputElement
  emit('update:modelValue', input.value === '' || !Number.isFinite(input.valueAsNumber)
    ? null
    : input.valueAsNumber)
}
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
      <input
        v-bind="attrs"
        :id="inputId"
        class="plugin-field-control plugin-number-field"
        :value="modelValue ?? ''"
        :name="name || undefined"
        type="number"
        :inputmode="inputmode"
        :min="min"
        :max="max"
        :step="step"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describedBy"
        @input="updateValue"
        @blur="emit('blur', $event)"
      />
    </template>
  </PluginFieldShell>
</template>
