<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  inputId: string
  label: string
  description?: string
  error?: string
  required?: boolean
}>(), {
  description: '',
  error: '',
  required: false,
})

const descriptionId = computed(() => `${props.inputId}-description`)
const errorId = computed(() => `${props.inputId}-error`)
const describedBy = computed(() => [
  props.description ? descriptionId.value : '',
  props.error ? errorId.value : '',
].filter(Boolean).join(' ') || undefined)
</script>

<template>
  <label class="plugin-field" :for="inputId">
    <span class="plugin-field-label">
      {{ label }}<b v-if="required" aria-hidden="true">*</b>
    </span>
    <slot :described-by="describedBy" />
    <small v-if="description" :id="descriptionId" class="plugin-field-description">
      {{ description }}
    </small>
    <small v-if="error" :id="errorId" class="plugin-field-error" role="alert">
      {{ error }}
    </small>
  </label>
</template>

<style scoped>
.plugin-field {
  min-width: 0;
  display: grid;
  gap: 7px;
  color: var(--text);
}

.plugin-field-label {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  color: var(--muted);
  font-size: 10px;
  font-weight: 800;
}

.plugin-field-label b { color: var(--red); }

:deep(.plugin-field-control) {
  width: 100%;
  min-width: 0;
  min-height: 48px;
  border: 1px solid var(--line);
  border-radius: var(--radius-control);
  outline: 0;
  padding: 0 14px;
  color: var(--text);
  background: var(--surface-inset);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 24%, transparent);
  font: inherit;
  font-size: 14px;
  transition: border-color .15s ease, box-shadow .15s ease;
}

:deep(.plugin-field-control:focus) {
  border-color: var(--gold);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--gold) 16%, transparent);
}

:deep(.plugin-field-control[aria-invalid="true"]) { border-color: var(--red); }
:deep(.plugin-field-control:disabled) { cursor: not-allowed; opacity: .58; }

.plugin-field-description,
.plugin-field-error {
  font-size: 9px;
  line-height: 1.5;
}

.plugin-field-description { color: var(--muted); }
.plugin-field-error { color: var(--red); }
</style>
