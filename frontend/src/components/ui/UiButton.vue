<script setup lang="ts">
export type UiButtonVariant = 'primary' | 'secondary' | 'danger'

withDefaults(defineProps<{
  variant?: UiButtonVariant
  type?: 'button' | 'submit' | 'reset'
  block?: boolean
  compact?: boolean
}>(), {
  variant: 'secondary',
  type: 'button',
  block: false,
  compact: false,
})
</script>

<template>
  <button
    :type="type"
    class="ui-button"
    data-ui-interaction="lift"
    :class="[
      `ui-button--${variant}`,
      {
        'ui-button--block': block,
        'ui-button--compact': compact,
      },
    ]"
  >
    <slot />
  </button>
</template>

<style scoped>
.ui-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-height: 50px;
  border: 1px solid var(--line);
  border-radius: var(--radius-control);
  padding: 0 18px;
  color: var(--text);
  background: var(--control-surface), var(--surface-inset);
  box-shadow:
    var(--shadow-contact),
    inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 62%, transparent),
    inset 0 0 0 1px color-mix(in srgb, var(--line-bright) 10%, transparent);
  font-size: 14px;
  font-weight: 850;
  cursor: pointer;
}

.ui-button--primary {
  --ui-button-hover-lift: -2px;
  border-color: color-mix(in srgb, var(--primary-start) 58%, var(--primary-end));
  color: var(--primary-text);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.2), transparent 42%),
    linear-gradient(145deg, var(--primary-start), var(--primary-end));
  box-shadow:
    0 12px 30px color-mix(in srgb, var(--accent) 22%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.64),
    inset 0 -1px 0 color-mix(in srgb, var(--accent-deep) 64%, transparent);
}

.ui-button--danger {
  border-color: color-mix(in srgb, var(--red) 58%, var(--line));
  color: #fff;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.12), transparent 42%),
    linear-gradient(135deg, color-mix(in srgb, var(--red) 88%, #cf5f60), #9c3740);
  box-shadow:
    0 12px 27px color-mix(in srgb, var(--red) 22%, transparent),
    inset 0 1px 0 rgba(255, 255, 255, 0.24);
}

.ui-button--block {
  width: 100%;
}

.ui-button--compact {
  min-height: 42px;
  padding: 8px 15px;
  font-size: 12px;
}

.ui-button:disabled {
  cursor: not-allowed;
  opacity: .58;
}

@media (hover: hover) {
  .ui-button:hover:not(:disabled) {
    border-color: var(--line-strong);
  }

  .ui-button--primary:hover:not(:disabled) {
    box-shadow:
      0 16px 34px color-mix(in srgb, var(--accent) 30%, transparent),
      inset 0 1px 0 rgba(255, 255, 255, 0.68);
  }

  .ui-button--danger:hover:not(:disabled) {
    border-color: color-mix(in srgb, var(--red) 78%, var(--line));
    box-shadow: 0 15px 31px color-mix(in srgb, var(--red) 28%, transparent);
  }
}

:global(:root[data-color-scheme="light"]) .ui-button:disabled {
  opacity: 1;
  border-color: color-mix(in srgb, var(--text) 22%, transparent);
  color: var(--disabled-text);
  background: linear-gradient(145deg, var(--disabled-bg-start), var(--disabled-bg-end));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.78),
    0 2px 5px rgba(67, 78, 85, 0.1);
}
</style>
