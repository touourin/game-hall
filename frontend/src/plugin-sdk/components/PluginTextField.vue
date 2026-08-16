<script setup lang="ts">
import { computed, useAttrs, useId } from 'vue'
import PluginFieldShell from './PluginFieldShell.vue'
import type { PluginTextFieldProps } from '../types'

defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<PluginTextFieldProps>(), {
  id: '',
  name: '',
  type: 'text',
  inputmode: 'text',
  autocomplete: '',
  placeholder: '',
  description: '',
  error: '',
  maxlength: undefined,
  disabled: false,
  required: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  blur: [event: FocusEvent]
}>()

const attrs = useAttrs()
const generatedId = `plugin-text-field-${useId()}`
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
      <input
        v-bind="attrs"
        :id="inputId"
        class="plugin-field-control plugin-text-field"
        :value="modelValue"
        :name="name || undefined"
        :type="type"
        :inputmode="inputmode"
        :autocomplete="autocomplete || undefined"
        :placeholder="placeholder"
        :maxlength="maxlength"
        :disabled="disabled"
        :required="required"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describedBy"
        @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        @blur="emit('blur', $event)"
      />
    </template>
  </PluginFieldShell>
</template>
