<script setup lang="ts">
import { AlertTriangle, Inbox, Info, LoaderCircle } from '@lucide/vue'
import PluginButton from './PluginButton.vue'
import type { PluginStatePanelProps } from '../types'

withDefaults(defineProps<PluginStatePanelProps>(), {
  description: '',
  tone: 'info',
  actionLabel: '',
  busy: false,
})

defineEmits<{ action: [] }>()
</script>

<template>
  <section
    class="plugin-state-panel"
    :class="`plugin-state-panel--${tone}`"
    :role="tone === 'error' ? 'alert' : 'status'"
    :aria-busy="tone === 'loading' || busy ? 'true' : undefined"
  >
    <span class="plugin-state-panel-icon" aria-hidden="true">
      <slot name="icon">
        <LoaderCircle v-if="tone === 'loading'" class="plugin-state-panel-spinner" :size="26" />
        <Inbox v-else-if="tone === 'empty'" :size="26" />
        <AlertTriangle v-else-if="tone === 'error'" :size="26" />
        <Info v-else :size="26" />
      </slot>
    </span>
    <div class="plugin-state-panel-copy">
      <strong>{{ title }}</strong>
      <p v-if="description">{{ description }}</p>
      <slot />
    </div>
    <slot name="action">
      <PluginButton
        v-if="actionLabel"
        compact
        :variant="tone === 'error' ? 'danger' : 'secondary'"
        :disabled="busy"
        @click="$emit('action')"
      >
        {{ actionLabel }}
      </PluginButton>
    </slot>
  </section>
</template>

<style scoped>
.plugin-state-panel {
  width: 100%;
  min-width: 0;
  min-height: 150px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 12px;
  border: 1px dashed color-mix(in srgb, var(--accent) 28%, var(--line));
  border-radius: var(--radius-card);
  padding: clamp(20px, 5vw, 34px);
  color: var(--text);
  background: color-mix(in srgb, var(--surface-inset) 72%, transparent);
  text-align: center;
}

.plugin-state-panel-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 15px;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, transparent);
}

.plugin-state-panel--error {
  border-color: color-mix(in srgb, var(--red) 42%, var(--line));
}

.plugin-state-panel--error .plugin-state-panel-icon {
  color: var(--red);
  background: color-mix(in srgb, var(--red) 10%, transparent);
}

.plugin-state-panel-copy { min-width: 0; }
.plugin-state-panel-copy strong { display: block; font-size: 15px; }
.plugin-state-panel-copy p { margin: 6px 0 0; color: var(--muted); font-size: 11px; line-height: 1.6; }

.plugin-state-panel-spinner { animation: plugin-state-spin .9s linear infinite; }

@keyframes plugin-state-spin { to { transform: rotate(360deg); } }
</style>
