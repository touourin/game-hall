<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ size: number }>()

const coordinates = computed(() =>
  Array.from({ length: props.size }, (_, index) => index + 0.5),
)
const lastCoordinate = computed(() => props.size - 0.5)
</script>

<template>
  <div
    class="intersection-board"
    :style="{ '--board-size': size }"
  >
    <div class="intersection-board__stage">
      <svg
        class="intersection-board__lattice"
        :viewBox="`0 0 ${size} ${size}`"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <template v-for="coordinate in coordinates" :key="coordinate">
          <line
            x1="0.5"
            :x2="lastCoordinate"
            :y1="coordinate"
            :y2="coordinate"
          />
          <line
            :x1="coordinate"
            :x2="coordinate"
            y1="0.5"
            :y2="lastCoordinate"
          />
        </template>
      </svg>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.intersection-board {
  --board-size: 19;
  --board-padding: 12px;
  --board-border-width: 5px;
  --board-max-width: 700px;
  position: relative;
  isolation: isolate;
  width: min(100%, var(--board-max-width));
  box-sizing: border-box;
  overflow: hidden;
  padding: var(--board-padding);
  border: var(--board-border-width) solid var(--game-board-frame, #74451f);
  border-radius: var(--radius-card);
  background-color: var(--game-board-surface, #d5a45d);
  background-image:
    linear-gradient(
      145deg,
      color-mix(in srgb, white 10%, transparent),
      transparent 31%,
      color-mix(in srgb, black 9%, transparent)
    ),
    var(
      --game-board-texture,
      repeating-linear-gradient(90deg, transparent 0 31px, rgba(88, 47, 17, .035) 32px)
    );
  box-shadow:
    inset 0 0 0 1px var(--game-board-highlight, rgba(255, 224, 157, .42)),
    inset 0 0 0 5px color-mix(in srgb, var(--game-board-frame, #74451f) 25%, transparent),
    inset 0 16px 30px color-mix(in srgb, white 7%, transparent),
    inset 0 -18px 34px color-mix(in srgb, black 13%, transparent),
    0 3px 0 color-mix(in srgb, var(--game-board-frame, #74451f) 72%, black),
    var(--shadow-raised),
    var(
      --board-status-ring,
      0 0 0 1px color-mix(in srgb, var(--gold) 24%, transparent)
    );
}

.intersection-board::before {
  content: '';
  pointer-events: none;
  position: absolute;
  z-index: 0;
  inset: 4px;
  border: 1px solid color-mix(in srgb, var(--game-board-highlight, #f1cd88) 66%, transparent);
  border-radius: calc(var(--radius-card) - 7px);
  box-shadow: inset 0 0 26px rgba(54, 27, 8, .12);
}

.intersection-board__stage {
  position: relative;
  z-index: 1;
  isolation: isolate;
  width: 100%;
  min-width: 0;
  min-height: 0;
  aspect-ratio: 1;
  display: grid;
  grid-template-columns: repeat(var(--board-size), minmax(0, 1fr));
  grid-template-rows: repeat(var(--board-size), minmax(0, 1fr));
}

.intersection-board__lattice {
  pointer-events: none;
  position: absolute;
  z-index: 1;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}

.intersection-board__lattice line {
  stroke: color-mix(in srgb, var(--game-board-line, #65401f) 90%, transparent);
  stroke-width: 1.1;
  vector-effect: non-scaling-stroke;
  shape-rendering: geometricPrecision;
}

:slotted(button) {
  min-width: 0;
  min-height: 0;
  margin: 0;
  appearance: none;
  -webkit-appearance: none;
  touch-action: manipulation;
  z-index: 2;
}
</style>
