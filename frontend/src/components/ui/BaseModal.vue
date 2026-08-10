<script setup lang="ts">
import { X } from '@lucide/vue'
import { nextTick, onBeforeUnmount, onMounted, ref, useId, useSlots } from 'vue'

const props = withDefaults(defineProps<{
  title?: string
  description?: string
  ariaLabel?: string
  panelClass?: string
  closeOnBackdrop?: boolean
  closeLabel?: string
}>(), {
  title: '',
  description: '',
  ariaLabel: '',
  panelClass: '',
  closeOnBackdrop: true,
  closeLabel: '关闭弹窗',
})

const emit = defineEmits<{ close: [] }>()
const slots = useSlots()
const panel = ref<HTMLElement | null>(null)
const titleId = `base-modal-title-${useId()}`
let previousFocus: HTMLElement | null = null

const focusableSelector = [
  'button:not([disabled])',
  'a[href]',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

function close() {
  emit('close')
}

function handleBackdrop() {
  if (props.closeOnBackdrop) close()
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.preventDefault()
    close()
    return
  }
  if (event.key !== 'Tab' || !panel.value) return

  const focusable = [...panel.value.querySelectorAll<HTMLElement>(focusableSelector)]
    .filter((element) => !element.hidden && element.getAttribute('aria-hidden') !== 'true')
  if (!focusable.length) {
    event.preventDefault()
    panel.value.focus()
    return
  }

  const first = focusable[0]!
  const last = focusable.at(-1)!
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

onMounted(async () => {
  previousFocus = document.activeElement instanceof HTMLElement
    ? document.activeElement
    : null
  window.addEventListener('keydown', handleKeydown)
  await nextTick()
  panel.value?.querySelector<HTMLElement>(focusableSelector)?.focus()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  previousFocus?.focus()
})
</script>

<template>
  <Teleport to="body">
    <div class="modal-backdrop base-modal-backdrop" @click.self="handleBackdrop">
      <section
        ref="panel"
        class="modal-card base-modal-card"
        :class="panelClass"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="title || slots.title ? titleId : undefined"
        :aria-label="title || slots.title ? undefined : ariaLabel"
        tabindex="-1"
      >
        <button class="modal-close" type="button" :aria-label="closeLabel" @click="close">
          <X :size="20" />
        </button>
        <span v-if="slots.icon" class="modal-icon"><slot name="icon" /></span>
        <h2 v-if="title || slots.title" :id="titleId"><slot name="title">{{ title }}</slot></h2>
        <p v-if="description || slots.description"><slot name="description">{{ description }}</slot></p>
        <slot />
        <footer v-if="slots.footer" class="base-modal-footer"><slot name="footer" /></footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.base-modal-card:focus { outline: none; }
.base-modal-footer { display: flex; justify-content: flex-end; gap: 9px; margin-top: 18px; }
@media (max-width: 600px) {
  .base-modal-backdrop { align-items: end; padding: max(10px, env(safe-area-inset-top)) 10px max(10px, env(safe-area-inset-bottom)); }
  .base-modal-card { width: 100%; max-height: min(92dvh, 820px); border-radius: 10px 10px 7px 7px; }
  .base-modal-footer { position: sticky; bottom: 0; margin-right: -12px; margin-bottom: -12px; margin-left: -12px; padding: 12px; background: linear-gradient(180deg, transparent, var(--modal-surface) 28%); }
}
</style>
