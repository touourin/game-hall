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
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 18px;
  margin-bottom: 20px;
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
  font-size: clamp(24px, 4vw, 38px);
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
  }

  .room-page-actions {
    grid-column: 1 / -1;
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
