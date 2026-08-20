<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ChevronRight, Clock3, RotateCcw } from '@lucide/vue'

const props = withDefaults(defineProps<{
  activeGameName?: string | null
  activeRoomCode?: string | null
}>(), {
  activeGameName: null,
  activeRoomCode: null,
})

const emit = defineEmits<{
  resume: []
}>()

const timeFormatter = new Intl.DateTimeFormat('zh-CN', {
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})
const dateFormatter = new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
})
const weekdayFormatter = new Intl.DateTimeFormat('zh-CN', {
  weekday: 'long',
})
const currentTime = ref(new Date())
const timeText = computed(() => timeFormatter.format(currentTime.value))
const dateText = computed(() => dateFormatter.format(currentTime.value))
const weekdayText = computed(() => weekdayFormatter.format(currentTime.value))
const hasActiveRoom = computed(() => Boolean(props.activeRoomCode))
let minuteTimer: ReturnType<typeof window.setTimeout> | null = null

function scheduleNextMinute() {
  const delay = 60_000 - (Date.now() % 60_000) + 20
  minuteTimer = window.setTimeout(() => {
    currentTime.value = new Date()
    scheduleNextMinute()
  }, delay)
}

onMounted(scheduleNextMinute)
onBeforeUnmount(() => {
  if (minuteTimer !== null) window.clearTimeout(minuteTimer)
})
</script>

<template>
  <section
    class="hall-clock-widget"
    :class="{ 'hall-clock-widget--active': hasActiveRoom }"
    :aria-label="hasActiveRoom ? '进行中的对局' : `当前时间 ${timeText}，${dateText} ${weekdayText}`"
  >
    <button
      v-if="hasActiveRoom"
      type="button"
      class="hall-clock-return"
      :aria-label="`返回${activeGameName || '未结束'}对局，房间 ${activeRoomCode}`"
      @click="emit('resume')"
    >
      <span class="hall-clock-icon" aria-hidden="true"><RotateCcw :size="18" /></span>
      <span class="hall-clock-copy">
        <small>对局进行中</small>
        <strong>{{ activeGameName || '未结束对局' }}</strong>
        <em>房间 {{ activeRoomCode }}</em>
      </span>
      <span class="hall-clock-action">返回对局<ChevronRight :size="16" aria-hidden="true" /></span>
    </button>

    <div v-else class="hall-clock-face" role="timer" aria-live="off">
      <span class="hall-clock-icon" aria-hidden="true"><Clock3 :size="18" /></span>
      <span class="hall-clock-time">
        <small>LOCAL TIME</small>
        <time :datetime="currentTime.toISOString()">{{ timeText }}</time>
      </span>
      <span class="hall-clock-date">
        <strong>{{ dateText }}</strong>
        <small>{{ weekdayText }}</small>
      </span>
    </div>
  </section>
</template>

<style scoped>
.hall-clock-widget {
  min-width: 270px;
  height: 54px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius-control);
  background: color-mix(in srgb, var(--surface-inset) 72%, transparent);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 36%, transparent);
}

.hall-clock-widget--active {
  border-color: color-mix(in srgb, var(--accent) 38%, var(--line));
  background: color-mix(in srgb, var(--accent) 7%, var(--surface-inset));
}

.hall-clock-face,
.hall-clock-return {
  display: grid;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 100%;
  padding: 6px 11px;
}

.hall-clock-face {
  grid-template-columns: 36px auto minmax(72px, 1fr);
}

.hall-clock-return {
  grid-template-columns: 36px minmax(0, 1fr) auto;
  min-width: 0;
  border: 0;
  color: var(--text);
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.hall-clock-icon {
  display: grid;
  place-items: center;
  width: 36px;
  aspect-ratio: 1;
  border-radius: 10px;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, var(--surface-soft));
}

.hall-clock-copy {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: baseline;
  min-width: 0;
}

.hall-clock-copy small {
  grid-column: 1 / -1;
  margin-bottom: 1px;
  color: var(--accent);
  font-size: 8px;
  font-weight: 800;
  letter-spacing: .06em;
}

.hall-clock-copy strong,
.hall-clock-copy em {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hall-clock-time {
  display: grid;
  gap: 1px;
}

.hall-clock-time small {
  color: var(--accent);
  font-size: 7px;
  font-weight: 820;
  letter-spacing: .12em;
}

.hall-clock-time time {
  color: var(--text);
  font-size: 22px;
  font-variant-numeric: tabular-nums;
  font-weight: 820;
  letter-spacing: -.025em;
  line-height: 1;
}

.hall-clock-copy strong {
  font-size: 12px;
}

.hall-clock-copy em {
  margin-left: 8px;
  color: var(--muted);
  font-size: 9px;
  font-style: normal;
}

.hall-clock-date {
  display: grid;
  justify-self: end;
  min-width: 74px;
  border-left: 1px solid var(--line);
  padding-left: 13px;
  text-align: right;
}

.hall-clock-date strong {
  color: var(--text-soft);
  font-size: 10px;
  font-weight: 760;
}

.hall-clock-date small {
  margin-top: 2px;
  color: var(--muted);
  font-size: 8px;
}

.hall-clock-action {
  display: inline-flex;
  align-items: center;
  color: var(--text-soft);
  font-size: 9px;
  font-weight: 760;
  white-space: nowrap;
}

@media (hover: hover) {
  .hall-clock-return:hover {
    background: color-mix(in srgb, var(--accent) 6%, transparent);
  }
}

@media (max-width: 520px) {
  .hall-clock-widget {
    min-width: 0;
  }

  .hall-clock-action {
    font-size: 0;
  }
}
</style>
