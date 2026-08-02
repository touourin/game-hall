<script setup lang="ts">
defineProps<{
  eyebrow: string
  title: string
}>()
</script>

<template>
  <header class="room-page-header">
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
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 20px;
}

.room-page-copy {
  flex: 1 1 280px;
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
  flex: 0 0 auto;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 680px) {
  .room-page-header {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 11px;
  }

  .room-page-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
