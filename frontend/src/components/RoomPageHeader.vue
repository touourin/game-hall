<script setup lang="ts">
defineProps<{
  eyebrow: string
  title: string
}>()
</script>

<template>
  <header class="room-page-header">
    <div class="room-page-navigation">
      <slot name="navigation" />
    </div>
    <div class="room-page-copy">
      <small>{{ eyebrow }}</small>
      <div class="room-page-title-row">
        <h1>{{ title }}</h1>
        <slot name="details" />
      </div>
    </div>
    <div class="room-page-actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.room-page-header {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 18px;
  min-height: 82px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--line);
  padding: 10px 0 15px;
}

.room-page-header::after {
  position: absolute;
  right: 0;
  bottom: -1px;
  left: 0;
  height: 1px;
  background: linear-gradient(90deg, var(--gold), var(--accent-secondary) 34%, transparent 72%);
  content: '';
}

.room-page-navigation {
  align-self: start;
}

.room-page-copy {
  min-width: 0;
}

.room-page-copy > small {
  display: block;
  color: var(--gold);
  font-family: ui-monospace, "SFMono-Regular", Consolas, monospace;
  font-size: 8px;
  font-weight: 800;
  letter-spacing: .14em;
}

.room-page-title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 9px;
  margin-top: 4px;
}

.room-page-title-row h1 {
  margin: 0;
  font-size: clamp(24px, 4vw, 36px);
  font-weight: 800;
  letter-spacing: -.025em;
}

.room-page-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 680px) {
  .room-page-header {
    grid-template-columns: auto minmax(0, 1fr);
    gap: 11px;
    min-height: 0;
    padding-top: 5px;
  }

  .room-page-actions {
    grid-column: 1 / -1;
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
