<script setup lang="ts">
import type { ModeGuideContent } from './uiTypes'

defineProps<{ content: ModeGuideContent }>()
</script>

<template>
  <article class="mode-guide" :aria-label="content.ariaLabel">
    <header>
      <small>{{ content.eyebrow }}</small>
      <h3>{{ content.title }}</h3>
      <p>{{ content.story }}</p>
    </header>
    <section class="mode-guide-feature">
      <div><small>{{ content.feature.label }}</small><strong>{{ content.feature.title }}</strong></div>
      <p>{{ content.feature.description }}</p>
      <ul><li v-for="detail in content.feature.details" :key="detail.label"><b>{{ detail.label }}</b> {{ detail.text }}</li></ul>
    </section>
    <section class="mode-guide-flow">
      <h4>{{ content.flowTitle }}</h4>
      <ol>
        <li v-for="(step, index) in content.steps" :key="step.title">
          <span>{{ index + 1 }}</span><p><b>{{ step.title }}</b>{{ step.text }}</p>
        </li>
      </ol>
    </section>
    <footer>{{ content.footer }}</footer>
  </article>
</template>

<style scoped>
.mode-guide { display: grid; gap: 12px; color: var(--text); text-align: left; }
.mode-guide > header { border: 1px solid color-mix(in srgb, var(--gold) 24%, var(--line)); border-radius: 15px; padding: 15px; background: radial-gradient(circle at 92% 0%, color-mix(in srgb, var(--gold) 12%, transparent), transparent 40%), rgba(var(--surface-deep-rgb), .72); }
.mode-guide > header small, .mode-guide-feature small { color: var(--gold); font-size: 9px; font-weight: 850; letter-spacing: .12em; }
.mode-guide h3 { margin: 7px 0 8px; font-family: "Songti SC", "STSong", serif; font-size: 20px; letter-spacing: .04em; }
.mode-guide p { margin: 0; color: var(--text-soft); font-size: 11px; line-height: 1.7; }
.mode-guide-feature { border: 1px solid color-mix(in srgb, var(--red) 30%, var(--line)); border-radius: 15px; padding: 14px; background: color-mix(in srgb, var(--red) 7%, var(--surface)); }
.mode-guide-feature > div { display: grid; gap: 3px; margin-bottom: 8px; }
.mode-guide-feature strong { color: var(--red); font-family: "Songti SC", "STSong", serif; font-size: 18px; }
.mode-guide-feature ul { display: grid; gap: 7px; margin: 11px 0 0; padding-left: 18px; color: var(--text-soft); font-size: 10px; line-height: 1.55; }
.mode-guide-feature b, .mode-guide-flow b { color: var(--text); }
.mode-guide-flow { border: 1px solid var(--line); border-radius: 15px; padding: 14px; background: rgba(var(--surface-deep-rgb), .58); }
.mode-guide-flow h4 { margin: 0 0 11px; color: var(--gold); font-size: 12px; }
.mode-guide-flow ol { display: grid; gap: 9px; margin: 0; padding: 0; list-style: none; }
.mode-guide-flow li { display: grid; grid-template-columns: 25px minmax(0, 1fr); align-items: start; gap: 9px; }
.mode-guide-flow li > span { display: grid; place-items: center; width: 25px; height: 25px; border: 1px solid color-mix(in srgb, var(--gold) 35%, var(--line)); border-radius: 8px; color: var(--gold); background: color-mix(in srgb, var(--gold) 8%, transparent); font-size: 10px; font-weight: 900; }
.mode-guide footer { border-radius: 11px; padding: 10px 12px; color: var(--muted); background: color-mix(in srgb, var(--gold) 6%, transparent); font-size: 10px; line-height: 1.55; }
@media (max-width: 480px) { .mode-guide > header, .mode-guide-feature, .mode-guide-flow { padding: 12px; } .mode-guide h3 { font-size: 18px; } }
</style>
