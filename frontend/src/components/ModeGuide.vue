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
    <section class="mode-guide-quick-start">
      <div>
        <small>{{ content.quickStart.label }}</small>
        <h4>{{ content.quickStart.title }}</h4>
        <p>{{ content.quickStart.description }}</p>
      </div>
      <ol>
        <li v-for="(step, index) in content.quickStart.steps" :key="step.title">
          <span>{{ index + 1 }}</span>
          <p><b>{{ step.title }}</b>{{ step.text }}</p>
        </li>
      </ol>
    </section>
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
    <section class="mode-guide-complete-rules">
      <header>
        <small>完整规则</small>
        <h4>从开局信息到终局结算</h4>
        <p>以下规则与当前游戏实现一致，可直接作为开局说明和争议判定依据。</p>
      </header>
      <section v-for="section in content.ruleSections" :key="section.title">
        <h5>{{ section.title }}</h5>
        <p v-if="section.description">{{ section.description }}</p>
        <div v-if="section.table" class="mode-guide-table-wrap">
          <table>
            <thead>
              <tr><th v-for="header in section.table.headers" :key="header">{{ header }}</th></tr>
            </thead>
            <tbody>
              <tr v-for="(row, rowIndex) in section.table.rows" :key="rowIndex">
                <td
                  v-for="(cell, cellIndex) in row"
                  :key="cellIndex"
                  :data-label="section.table.headers[cellIndex]"
                >
                  {{ cell }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <ul v-if="section.bullets?.length">
          <li v-for="bullet in section.bullets" :key="`${bullet.label}-${bullet.text}`">
            <b v-if="bullet.label">{{ bullet.label }}</b>{{ bullet.label ? '：' : '' }}{{ bullet.text }}
          </li>
        </ul>
      </section>
    </section>
    <section class="mode-guide-background">
      <header>
        <small>{{ content.background.label }}</small>
        <h4>{{ content.background.title }}</h4>
      </header>
      <p v-for="paragraph in content.background.paragraphs" :key="paragraph">{{ paragraph }}</p>
    </section>
    <footer>{{ content.footer }}</footer>
  </article>
</template>

<style scoped>
.mode-guide { min-width: 0; container-type: inline-size; display: grid; gap: 12px; color: var(--text); text-align: left; }
.mode-guide > *, .mode-guide-complete-rules, .mode-guide-complete-rules > section { min-width: 0; }
.mode-guide > header { border: 1px solid color-mix(in srgb, var(--accent) 24%, var(--line)); border-radius: 15px; padding: 15px; background: radial-gradient(circle at 92% 0%, color-mix(in srgb, var(--accent) 12%, transparent), transparent 40%), rgba(var(--surface-deep-rgb), .72); }
.mode-guide > header small, .mode-guide-feature small { color: var(--accent); font-size: 9px; font-weight: 850; letter-spacing: .12em; }
.mode-guide h3 { margin: 7px 0 8px; font-family: "Songti SC", "STSong", serif; font-size: 20px; letter-spacing: .04em; }
.mode-guide p { margin: 0; color: var(--text-soft); font-size: 11px; line-height: 1.7; }
.mode-guide-quick-start { border: 1px solid color-mix(in srgb, var(--accent) 46%, var(--line)); border-radius: 15px; padding: 14px; background: color-mix(in srgb, var(--accent) 9%, var(--surface)); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--accent) 7%, transparent); }
.mode-guide-quick-start > div { margin-bottom: 12px; }
.mode-guide-quick-start small, .mode-guide-complete-rules > header small, .mode-guide-background small { color: var(--accent); font-size: 9px; font-weight: 850; letter-spacing: .12em; }
.mode-guide-quick-start h4, .mode-guide-complete-rules h4, .mode-guide-background h4 { margin: 5px 0 7px; font-family: "Songti SC", "STSong", serif; font-size: 18px; }
.mode-guide-quick-start ol { display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; }
.mode-guide-quick-start li { display: grid; grid-template-columns: 25px minmax(0, 1fr); align-items: start; gap: 9px; }
.mode-guide-quick-start li > span { display: grid; place-items: center; width: 25px; height: 25px; border-radius: 8px; color: var(--accent-contrast); background: var(--accent); font-size: 10px; font-weight: 900; }
.mode-guide-quick-start li b { color: var(--text); }
.mode-guide-feature { border: 1px solid color-mix(in srgb, var(--red) 30%, var(--line)); border-radius: 15px; padding: 14px; background: color-mix(in srgb, var(--red) 7%, var(--surface)); }
.mode-guide-feature > div { display: grid; gap: 3px; margin-bottom: 8px; }
.mode-guide-feature strong { color: var(--red); font-family: "Songti SC", "STSong", serif; font-size: 18px; }
.mode-guide-feature ul { display: grid; gap: 7px; margin: 11px 0 0; padding-left: 18px; color: var(--text-soft); font-size: 10px; line-height: 1.55; }
.mode-guide-feature b, .mode-guide-flow b { color: var(--text); }
.mode-guide-flow { border: 1px solid var(--line); border-radius: 15px; padding: 14px; background: rgba(var(--surface-deep-rgb), .58); }
.mode-guide-flow h4 { margin: 0 0 11px; color: var(--accent); font-size: 12px; }
.mode-guide-flow ol { display: grid; gap: 9px; margin: 0; padding: 0; list-style: none; }
.mode-guide-flow li { display: grid; grid-template-columns: 25px minmax(0, 1fr); align-items: start; gap: 9px; }
.mode-guide-flow li > span { display: grid; place-items: center; width: 25px; height: 25px; border: 1px solid color-mix(in srgb, var(--accent) 35%, var(--line)); border-radius: 8px; color: var(--accent); background: color-mix(in srgb, var(--accent) 8%, transparent); font-size: 10px; font-weight: 900; }
.mode-guide-complete-rules { display: grid; gap: 10px; }
.mode-guide-complete-rules > header { border-bottom: 1px solid var(--line); padding: 5px 2px 11px; }
.mode-guide-complete-rules > section { border: 1px solid var(--line); border-radius: 14px; padding: 13px; background: rgba(var(--surface-deep-rgb), .45); }
.mode-guide-complete-rules h5 { margin: 0 0 7px; color: var(--accent); font-size: 12px; }
.mode-guide-complete-rules ul { display: grid; gap: 7px; margin: 10px 0 0; padding-left: 18px; color: var(--text-soft); font-size: 10px; line-height: 1.65; }
.mode-guide-complete-rules li b { color: var(--text); }
.mode-guide-table-wrap { width: 100%; max-width: 100%; margin-top: 10px; overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; }
.mode-guide-table-wrap table { width: 100%; min-width: 620px; border-collapse: collapse; color: var(--text-soft); background: color-mix(in srgb, var(--surface-inset) 72%, transparent); font-size: 9px; line-height: 1.45; }
.mode-guide-table-wrap th, .mode-guide-table-wrap td { border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 7px 8px; text-align: left; vertical-align: top; }
.mode-guide-table-wrap th:last-child, .mode-guide-table-wrap td:last-child { border-right: 0; }
.mode-guide-table-wrap tbody tr:last-child td { border-bottom: 0; }
.mode-guide-table-wrap th { color: var(--text); background: color-mix(in srgb, var(--accent) 8%, var(--surface-inset)); white-space: nowrap; }
.mode-guide-background { border: 1px solid color-mix(in srgb, var(--accent) 30%, var(--line)); border-radius: 15px; padding: 15px; background: radial-gradient(circle at 90% 0%, color-mix(in srgb, var(--accent) 11%, transparent), transparent 34%), rgba(var(--surface-deep-rgb), .62); }
.mode-guide-background > header { margin-bottom: 10px; }
.mode-guide-background > p { color: var(--text-soft); font-size: 10.5px; line-height: 1.82; text-indent: 2em; }
.mode-guide-background > p + p { margin-top: 9px; }
.mode-guide footer { border-radius: 11px; padding: 10px 12px; color: var(--muted); background: color-mix(in srgb, var(--accent) 6%, transparent); font-size: 10px; line-height: 1.55; }
@container (min-width: 760px) {
  .mode-guide-quick-start ol, .mode-guide-flow ol { grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 28px; row-gap: 10px; }
  .mode-guide-quick-start li, .mode-guide-flow li { min-height: 42px; align-items: center; border-radius: 10px; padding: 8px 10px; background: color-mix(in srgb, var(--surface-inset) 42%, transparent); }
  .mode-guide-quick-start li:last-child:nth-child(odd) { grid-column: 1 / -1; width: calc(50% - 14px); justify-self: center; }
}
@container (max-width: 680px) {
  .mode-guide > header, .mode-guide-quick-start, .mode-guide-feature, .mode-guide-flow, .mode-guide-complete-rules > section, .mode-guide-background { padding: 12px; }
  .mode-guide h3 { font-size: 18px; }
  .mode-guide-quick-start h4, .mode-guide-complete-rules h4, .mode-guide-background h4 { font-size: 17px; }
  .mode-guide-table-wrap { border: 0; overflow: visible; }
  .mode-guide-table-wrap table, .mode-guide-table-wrap tbody { display: block; min-width: 0; background: transparent; }
  .mode-guide-table-wrap thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }
  .mode-guide-table-wrap tbody { display: grid; gap: 8px; }
  .mode-guide-table-wrap tr { display: grid; border: 1px solid var(--line); border-radius: 9px; overflow: hidden; background: color-mix(in srgb, var(--surface-inset) 72%, transparent); }
  .mode-guide-table-wrap td { display: grid; grid-template-columns: 66px minmax(0, 1fr); gap: 8px; border-right: 0; padding: 7px 8px; }
  .mode-guide-table-wrap td::before { color: var(--muted); font-weight: 800; content: attr(data-label); }
  .mode-guide-table-wrap tbody tr:last-child td:not(:last-child) { border-bottom: 1px solid var(--line); }
}
</style>
