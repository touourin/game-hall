<script setup lang="ts">
withDefaults(defineProps<{
  type?: 'button' | 'submit' | 'reset'
  compact?: boolean
}>(), {
  type: 'button',
  compact: false,
})
</script>

<template>
  <button
    :type="type"
    class="ui-icon-button"
    :class="{ 'ui-icon-button--compact': compact }"
  >
    <slot />
  </button>
</template>

<style scoped>
.ui-icon-button {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border: 1px solid var(--line);
  border-radius: 50%;
  padding: 0;
  color: var(--text-soft);
  background: var(--control-surface), var(--surface-inset);
  box-shadow:
    var(--shadow-contact),
    inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 66%, transparent),
    inset 0 0 0 1px color-mix(in srgb, var(--line-bright) 12%, transparent);
  cursor: pointer;
  touch-action: manipulation;
}

.ui-icon-button--compact {
  width: 34px;
  height: 34px;
}

.ui-icon-button:active:not(:disabled) {
  transform: translateY(1px);
}

@media (hover: hover) {
  .ui-icon-button:hover:not(:disabled) {
    border-color: var(--line-strong);
    color: var(--gold);
    transform: translateY(-1px);
  }
}

@media (max-width: 760px) {
  .ui-icon-button {
    min-width: 44px;
    min-height: 44px;
  }
}

:global(:root[data-theme="royal"]) .ui-icon-button {
  color: var(--text-soft);
}
</style>
