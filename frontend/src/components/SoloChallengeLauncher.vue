<script setup lang="ts">
import { computed, type Component } from 'vue'
import {
  CircleCheckBig,
  Gamepad2,
  Play,
  ShieldCheck,
  Sparkles,
} from '@lucide/vue'
import type { ArcadeGameKey } from '../types/arcade'
import { gameRegistration } from '../game-platform/registry'
import type { BuiltinGameSoloContent } from '../game-platform/types'
import { gameCatalogItem } from '../gameCatalog'
import GameRuleSettings from './GameRuleSettings.vue'

type RenderedSoloChallenge = BuiltinGameSoloContent & {
  icon: Component
  accent: string
}

const props = defineProps<{
  gameKey: ArcadeGameKey
  modelValue: Record<string, unknown>
  disabled?: boolean
  activeRoom?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, unknown>]
  start: []
}>()

const rules = computed({
  get: () => props.modelValue,
  set: (value: Record<string, unknown>) => emit('update:modelValue', value),
})

const gamePresentation = computed(
  () => gameRegistration(props.gameKey)?.presentation.solo,
)
const hasRules = computed(() => gamePresentation.value?.hasRuleSettings === true)
const catalogGame = computed(() => gameCatalogItem(props.gameKey))

const challenge = computed<RenderedSoloChallenge>(() => {
  const presentation = gamePresentation.value
  if (presentation) {
    return {
      icon: presentation.icon,
      accent: presentation.accent,
      ...presentation.content(props.modelValue),
    }
  }

  const game = catalogGame.value
  return {
    icon: Gamepad2,
    accent: '#7794a8',
    category: '社区单人挑战',
    kicker: '社区单人挑战',
    title: game?.name ?? '插件挑战',
    description: game?.description ?? '由社区插件提供的单人挑战。',
    button: `进入${game?.name ?? '插件挑战'}`,
    features: ['自动创建单人房间', '服务端规则验证', '独立战绩与排行'],
    metrics: [
      { label: '挑战人数', value: '1 人' },
      { label: '房间方式', value: '自动创建' },
      { label: '成绩记录', value: '独立统计' },
    ],
    stages: ['创建挑战', '完成目标', '记录成绩'],
    recordNote: '挑战完成后，公共房间系统会自动保存结果并更新排行榜。',
  }
})
</script>

<template>
  <section
    class="solo-launcher surface"
    :class="`solo-launcher-${gameKey}`"
    :style="{ '--solo-accent': challenge.accent }"
  >
    <div class="solo-story">
      <div class="solo-visual" aria-hidden="true">
        <span class="solo-orbit solo-orbit-outer"></span>
        <span class="solo-orbit solo-orbit-inner"></span>
        <span class="solo-emblem" data-testid="solo-challenge-icon">
          <component :is="challenge.icon" :size="34" :stroke-width="1.65" />
        </span>
        <Sparkles class="solo-spark solo-spark-first" :size="14" />
        <Sparkles class="solo-spark solo-spark-second" :size="10" />
      </div>

      <div class="solo-story-copy">
        <p class="solo-protocol"><span>{{ challenge.category }}</span><b>单人挑战</b></p>
        <p class="solo-kicker">{{ challenge.kicker }}</p>
        <h2>{{ challenge.title }}</h2>
        <p class="solo-description">{{ challenge.description }}</p>
      </div>

      <ul class="solo-feature-list" aria-label="挑战特性">
        <li v-for="feature in challenge.features" :key="feature">
          <CircleCheckBig :size="14" :stroke-width="1.8" />
          <span>{{ feature }}</span>
        </li>
      </ul>
    </div>

    <div class="solo-console">
      <header class="solo-console-header">
        <span><small>设置与挑战数据</small><strong>挑战控制台</strong></span>
        <b class="solo-ready"><i></i>可开始</b>
      </header>

      <form @submit.prevent="emit('start')">
        <GameRuleSettings
          v-if="hasRules"
          v-model="rules"
          :game-key="gameKey"
          class="solo-rule-settings"
        />

        <div class="solo-metric-grid" :class="{ 'with-rules': hasRules }">
          <div v-for="metric in challenge.metrics" :key="metric.label" class="solo-metric">
            <small>{{ metric.label }}</small>
            <strong>{{ metric.value }}</strong>
          </div>
        </div>

        <ol v-if="!hasRules" class="solo-stage-track" aria-label="挑战流程">
          <li v-for="(stage, index) in challenge.stages" :key="stage">
            <b>{{ index + 1 }}</b>
            <span>{{ stage }}</span>
          </li>
        </ol>

        <p v-if="activeRoom" class="solo-active-room-hint">请先返回并退出当前房间，再开始新的挑战。</p>

        <button type="submit" class="solo-start-button" :disabled="disabled">
          <span class="solo-start-icon"><Play :size="18" fill="currentColor" /></span>
          <span><small>创建挑战并开始计时</small><strong>{{ challenge.button }}</strong></span>
          <i aria-hidden="true"></i>
        </button>

        <p class="solo-record-note">
          <ShieldCheck :size="14" :stroke-width="1.8" />
          <span>{{ challenge.recordNote }}</span>
        </p>
      </form>
    </div>
  </section>
</template>

<style scoped>
.solo-launcher {
  --solo-accent: var(--accent);
  --solo-glow: color-mix(in srgb, var(--solo-accent) 24%, transparent);
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, .9fr) minmax(430px, 1.1fr);
  overflow: hidden;
  border-color: color-mix(in srgb, var(--solo-accent) 26%, var(--line));
  background:
    radial-gradient(circle at 12% 18%, color-mix(in srgb, var(--solo-accent) 9%, transparent), transparent 34%),
    linear-gradient(122deg, var(--surface-glass), var(--surface-primary) 54%),
    var(--material-pattern);
  box-shadow: var(--shadow-raised), inset 0 1px 0 var(--metal-edge);
  isolation: isolate;
}

.solo-launcher::before {
  position: absolute;
  z-index: -1;
  inset: 0;
  background: radial-gradient(ellipse at 30% 0, color-mix(in srgb, var(--solo-accent) 6%, transparent), transparent 38%);
  content: '';
  pointer-events: none;
}

.solo-launcher::after {
  position: absolute;
  z-index: 4;
  inset: 5px;
  border: 1px solid color-mix(in srgb, var(--line-bright) 12%, transparent);
  border-radius: calc(var(--radius-panel) - 5px);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--panel-highlight) 21%, transparent);
  content: '';
  pointer-events: none;
}

.solo-story {
  position: relative;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 38px 38px 34px;
}

.solo-visual {
  position: relative;
  width: 146px;
  height: 146px;
  display: grid;
  place-items: center;
  margin: 0 0 30px 8px;
}

.solo-visual::before {
  position: absolute;
  inset: 31px;
  border-radius: 26px;
  background: color-mix(in srgb, var(--solo-accent) 10%, var(--surface-inset));
  box-shadow: 0 0 42px var(--solo-glow);
  content: '';
  transform: rotate(45deg);
}

.solo-orbit {
  position: absolute;
  border: 1px solid color-mix(in srgb, var(--solo-accent) 28%, transparent);
  border-radius: 50%;
}

.solo-orbit::after {
  position: absolute;
  width: 5px;
  aspect-ratio: 1;
  border-radius: 50%;
  background: var(--solo-accent);
  box-shadow: 0 0 12px var(--solo-accent);
  content: '';
}

.solo-orbit-outer { inset: 8px; border-style: dashed; transform: rotate(-12deg); }
.solo-orbit-outer::after { top: 16px; right: 18px; }
.solo-orbit-inner { inset: 22px; opacity: .7; }
.solo-orbit-inner::after { right: -3px; bottom: 29px; }

.solo-emblem {
  position: relative;
  z-index: 1;
  width: 76px;
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--solo-accent) 54%, var(--line));
  border-radius: 24px;
  color: var(--solo-accent);
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--solo-accent) 16%, transparent), transparent),
    var(--surface-elevated);
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, white 15%, transparent),
    0 18px 38px color-mix(in srgb, var(--bg) 58%, transparent);
}

.solo-spark { position: absolute; color: var(--solo-accent); }
.solo-spark-first { top: 20px; right: 3px; }
.solo-spark-second { bottom: 25px; left: 13px; opacity: .65; }

.solo-story-copy { min-width: 0; }
.solo-protocol { display: flex; align-items: center; gap: 10px; margin: 0 0 17px; color: var(--solo-accent); font-size: 9px; font-weight: 900; letter-spacing: .18em; }
.solo-protocol span { white-space: nowrap; }
.solo-protocol::after { order: 2; width: 42px; height: 1px; background: color-mix(in srgb, var(--solo-accent) 40%, transparent); content: ''; }
.solo-protocol b { order: 3; color: var(--muted); font-size: 8px; white-space: nowrap; }
.solo-kicker { margin: 0 0 8px; color: var(--text-soft); font-size: 12px; font-weight: 800; letter-spacing: .08em; }
.solo-story h2 { max-width: 360px; margin: 0; font-size: clamp(27px, 2.4vw, 34px); font-weight: 800; letter-spacing: -.04em; line-height: 1.18; }
.solo-description { max-width: 410px; margin: 15px 0 0; color: var(--muted); font-size: 13px; line-height: 1.8; }

.solo-feature-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: auto 0 0;
  padding: 32px 0 0;
  list-style: none;
}

.solo-feature-list li { display: inline-flex; align-items: center; gap: 6px; border: 1px solid color-mix(in srgb, var(--solo-accent) 18%, var(--line)); border-radius: 999px; padding: 7px 9px; color: var(--text-soft); background: color-mix(in srgb, var(--solo-accent) 5%, var(--surface-inset)); font-size: 9px; font-weight: 760; }
.solo-feature-list svg { flex: 0 0 auto; color: var(--solo-accent); }

.solo-console {
  position: relative;
  display: flex;
  flex-direction: column;
  margin: 14px;
  border: 1px solid color-mix(in srgb, var(--solo-accent) 18%, var(--line));
  border-radius: calc(var(--radius-panel) - 7px);
  padding: 26px;
  background:
    linear-gradient(145deg, color-mix(in srgb, var(--solo-accent) 5%, transparent), transparent 38%),
    var(--surface-inset);
  box-shadow: inset 0 1px 0 var(--metal-edge);
}

.solo-console form { min-height: 0; display: flex; flex: 1; flex-direction: column; }

.solo-console-header { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-bottom: 23px; padding-bottom: 18px; border-bottom: 1px solid var(--line); }
.solo-console-header > span { display: grid; gap: 4px; }
.solo-console-header small { color: var(--solo-accent); font-size: 9px; font-weight: 850; letter-spacing: .05em; }
.solo-console-header strong { font-size: 16px; letter-spacing: .02em; }
.solo-ready { display: inline-flex; align-items: center; gap: 6px; border: 1px solid color-mix(in srgb, var(--solo-accent) 30%, var(--line)); border-radius: 999px; padding: 6px 9px; color: var(--solo-accent); background: color-mix(in srgb, var(--solo-accent) 7%, transparent); font-size: 8px; letter-spacing: .12em; }
.solo-ready i { width: 5px; aspect-ratio: 1; border-radius: 50%; background: currentColor; box-shadow: 0 0 9px currentColor; animation: solo-ready-pulse 1.8s ease-in-out infinite; }

.solo-rule-settings { margin-bottom: 20px; }
.solo-rule-settings :deep(.rule-setting-group) { gap: 13px; border: 0; padding: 0; }
.solo-rule-settings :deep(.rule-setting-group > header) { grid-template-columns: minmax(0, 1fr) auto; }
.solo-rule-settings :deep(.rule-setting-group > header strong) { font-size: 13px; }
.solo-rule-settings :deep(.rule-setting-group > header small) { max-width: 270px; font-size: 10px; }
.solo-rule-settings :deep(.rule-option-grid button) { min-height: 70px; border-radius: 13px; background: color-mix(in srgb, var(--surface-elevated) 42%, transparent); }
.solo-rule-settings :deep(.rule-option-grid button.active),
.solo-rule-settings :deep(.rule-segmented button.active) { border-color: color-mix(in srgb, var(--solo-accent) 60%, var(--line)); background: color-mix(in srgb, var(--solo-accent) 10%, var(--surface-inset)); }
.solo-rule-settings :deep(.rule-option-grid button.active::after) { border-color: var(--solo-accent); background: var(--solo-accent); }

.solo-metric-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.solo-metric-grid.with-rules { padding-top: 19px; border-top: 1px solid var(--line); }
.solo-metric { min-width: 0; display: grid; gap: 7px; border: 1px solid var(--line); border-radius: var(--radius-control); padding: 11px 12px; background: var(--surface-glass); box-shadow: inset 0 1px 0 var(--metal-edge); }
.solo-metric small { overflow: hidden; color: var(--muted); font-size: 8px; font-weight: 800; letter-spacing: .06em; text-overflow: ellipsis; white-space: nowrap; }
.solo-metric strong { overflow: hidden; color: var(--text); font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }

.solo-stage-track {
  position: relative;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 17px 0 0;
  border: 1px solid var(--line);
  border-radius: var(--radius-control);
  padding: 12px 10px;
  background: color-mix(in srgb, var(--surface-elevated) 24%, transparent);
  list-style: none;
}

.solo-stage-track::before { position: absolute; top: 22px; right: 17%; left: 17%; height: 1px; background: color-mix(in srgb, var(--solo-accent) 28%, var(--line)); content: ''; }
.solo-stage-track li { position: relative; z-index: 1; display: grid; justify-items: center; gap: 7px; color: var(--muted); font-size: 8px; font-weight: 800; }
.solo-stage-track b { width: 20px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--solo-accent) 42%, var(--line)); border-radius: 50%; color: var(--solo-accent); background: var(--surface-elevated); font-size: 8px; }

.solo-active-room-hint { margin: 15px 0 0; color: var(--muted); font-size: 11px; text-align: center; }

.solo-start-button {
  position: relative;
  width: 100%;
  min-height: 68px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  overflow: hidden;
  margin-top: 19px;
  border: 1px solid color-mix(in srgb, var(--solo-accent) 76%, white 12%);
  border-radius: var(--radius-control);
  padding: 0 18px;
  color: var(--accent-contrast);
  background: linear-gradient(125deg, color-mix(in srgb, var(--solo-accent) 76%, white), var(--solo-accent));
  box-shadow: var(--shadow-contact);
  text-align: left;
  cursor: pointer;
}

.solo-start-button::before { position: absolute; inset: 0; background: linear-gradient(110deg, transparent 20%, rgba(255, 255, 255, .2) 43%, transparent 61%); content: ''; transform: translateX(-120%); transition: transform 650ms ease; }
.solo-start-icon { position: relative; z-index: 1; width: 36px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 11px; background: color-mix(in srgb, var(--accent-contrast) 12%, transparent); }
.solo-start-button > span:nth-child(2) { position: relative; z-index: 1; display: grid; gap: 2px; }
.solo-start-button small { font-size: 7px; font-weight: 950; letter-spacing: .19em; opacity: .68; }
.solo-start-button strong { font-size: 14px; }
.solo-start-button > i { position: relative; z-index: 1; width: 28px; height: 1px; background: currentColor; opacity: .45; }
.solo-start-button > i::after { position: absolute; top: -3px; right: 0; width: 7px; height: 7px; border-top: 1px solid currentColor; border-right: 1px solid currentColor; content: ''; transform: rotate(45deg); }

.solo-record-note { display: flex; align-items: flex-start; justify-content: center; gap: 7px; margin: auto 4px 0; padding-top: 13px; color: var(--muted); font-size: 9px; line-height: 1.55; }
.solo-record-note svg { flex: 0 0 auto; margin-top: 1px; color: var(--solo-accent); }

@media (hover: hover) {
  .solo-start-button:hover:not(:disabled) { box-shadow: 0 20px 42px color-mix(in srgb, var(--solo-accent) 30%, transparent); transform: translateY(-2px); }
  .solo-start-button:hover:not(:disabled)::before { transform: translateX(120%); }
}

@keyframes solo-ready-pulse {
  50% { opacity: .35; transform: scale(.75); }
}

@media (max-width: 880px) {
  .solo-launcher { grid-template-columns: 1fr; }
  .solo-story { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 0 24px; padding-bottom: 28px; }
  .solo-visual { grid-row: 1 / span 2; width: 126px; height: 126px; margin: 2px 0 0; }
  .solo-story-copy { align-self: center; }
  .solo-feature-list { grid-column: 1 / -1; margin-top: 5px; padding-top: 22px; }
  .solo-console { margin-top: 0; }
}

@media (max-width: 600px) {
  .solo-story { display: block; padding: 25px 20px 23px; }
  .solo-visual { width: 112px; height: 112px; margin: 0 0 25px; }
  .solo-visual::before { inset: 27px; border-radius: 21px; }
  .solo-orbit-outer { inset: 5px; }
  .solo-orbit-inner { inset: 18px; }
  .solo-emblem { width: 62px; border-radius: 19px; }
  .solo-story h2 { font-size: 28px; }
  .solo-description { font-size: 12px; }
  .solo-feature-list { gap: 6px; padding-top: 22px; }
  .solo-feature-list li { padding: 6px 8px; font-size: 8px; }
  .solo-console { margin: 0 7px 7px; border-radius: 17px; padding: 20px 14px 17px; }
  .solo-console-header { margin-bottom: 18px; padding-bottom: 14px; }
  .solo-rule-settings :deep(.rule-setting-group > header) { grid-template-columns: 1fr; }
  .solo-rule-settings :deep(.rule-setting-group > header small) { text-align: left; }
  .solo-rule-settings :deep(.rule-option-grid.three) { grid-template-columns: 1fr; }
  .solo-rule-settings :deep(.rule-option-grid.three button:first-child) { grid-column: auto; }
  .solo-rule-settings :deep(.rule-segmented.six) { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .solo-metric { padding: 10px 8px; }
  .solo-metric strong { font-size: 11px; }
  .solo-start-button { min-height: 64px; padding: 0 13px; }
  .solo-start-button > i { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .solo-ready i { animation: none; }
  .solo-start-button::before { display: none; }
}

</style>
