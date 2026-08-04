<script setup lang="ts">
import { ArrowRight, Gamepad2, PackageOpen, ShieldCheck, X } from '@lucide/vue'
import type { GameCatalogItem } from '../types/arcade'

defineProps<{ games: readonly GameCatalogItem[] }>()
defineEmits<{
  close: []
  select: [game: GameCatalogItem]
}>()
</script>

<template>
  <div class="modal-backdrop" @click.self="$emit('close')" @keydown.esc="$emit('close')">
    <section class="modal-card third-party-games-modal" role="dialog" aria-modal="true" aria-label="第三方游戏">
      <button class="modal-close" type="button" aria-label="关闭第三方游戏" @click="$emit('close')">
        <X :size="20" />
      </button>

      <header class="third-party-modal-header">
        <span class="modal-icon"><Gamepad2 :size="25" /></span>
        <small>EXTENSION ARCADE</small>
        <h2>第三方游戏</h2>
        <p>独立插件接入，共用大厅的账号、房间、战绩与响应式界面。</p>
      </header>

      <div v-if="games.length" class="third-party-game-list">
        <button
          v-for="game in games"
          :key="game.key"
          type="button"
          class="third-party-game-option"
          @click="$emit('select', game)"
        >
          <span class="third-party-game-emblem"><Gamepad2 :size="20" /></span>
          <span>
            <small>{{ game.players }}</small>
            <strong>{{ game.name }}</strong>
            <em>{{ game.description }}</em>
          </span>
          <ArrowRight :size="18" />
        </button>
      </div>

      <div v-else class="third-party-empty" role="status">
        <PackageOpen :size="30" />
        <strong>暂未启用第三方游戏</strong>
        <span>插件安装并通过校验后，会自动出现在这里。</span>
      </div>

      <footer class="third-party-trust-note">
        <ShieldCheck :size="15" />
        <span>插件与内置游戏分目录维护，加载失败不会影响大厅。</span>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.third-party-games-modal { width: min(100%, 680px); max-height: min(88dvh, 720px); padding: clamp(24px, 4vw, 34px); text-align: left; }
.third-party-modal-header { padding: 2px 44px 22px 0; border-bottom: 1px solid var(--line); }.third-party-modal-header .modal-icon { margin: 0 0 13px; }.third-party-modal-header > small { display: block; margin-bottom: 7px; color: var(--gold); font-size: 8px; font-weight: 900; letter-spacing: .18em; }.third-party-modal-header h2 { margin: 0; font-family: "Songti SC", "STSong", serif; font-size: clamp(25px, 5vw, 32px); letter-spacing: .04em; }.third-party-modal-header p { margin: 8px 0 0; color: var(--muted); font-size: 12px; line-height: 1.65; }
.third-party-game-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; padding: 18px 0; }
.third-party-game-option { min-width: 0; display: grid; grid-template-columns: auto minmax(0,1fr) auto; align-items: center; gap: 11px; min-height: 96px; border: 1px solid var(--line); border-radius: 16px; padding: 13px; color: var(--text); background: radial-gradient(circle at 100% 0, color-mix(in srgb, var(--gold) 9%, transparent), transparent 42%), var(--surface-inset); text-align: left; cursor: pointer; }
.third-party-game-emblem { width: 42px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--gold) 30%, var(--line)); border-radius: 13px; color: var(--gold); background: color-mix(in srgb, var(--gold) 8%, var(--surface-elevated)); }.third-party-game-option > span:nth-child(2) { min-width: 0; display: grid; gap: 3px; }.third-party-game-option small { color: var(--gold); font-size: 8px; font-weight: 800; letter-spacing: .08em; }.third-party-game-option strong,.third-party-game-option em { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.third-party-game-option strong { font-family: "Songti SC", "STSong", serif; font-size: 17px; }.third-party-game-option em { color: var(--muted); font-size: 9px; font-style: normal; }.third-party-game-option > svg { color: var(--gold); }
.third-party-empty { min-height: 210px; display: grid; place-items: center; align-content: center; gap: 9px; margin: 18px 0; border: 1px dashed color-mix(in srgb, var(--gold) 32%, var(--line)); border-radius: 18px; padding: 24px; color: var(--muted); background: color-mix(in srgb, var(--gold) 3%, var(--surface-inset)); text-align: center; }.third-party-empty > svg { color: var(--gold); }.third-party-empty strong { color: var(--text); font-size: 15px; }.third-party-empty span { font-size: 11px; line-height: 1.55; }
.third-party-trust-note { display: flex; align-items: flex-start; gap: 7px; border-top: 1px solid var(--line); padding-top: 14px; color: var(--muted); font-size: 9px; line-height: 1.5; }.third-party-trust-note svg { flex: 0 0 auto; color: var(--gold); }
@media (hover: hover) { .third-party-game-option:hover { border-color: color-mix(in srgb, var(--gold) 48%, var(--line)); background-color: color-mix(in srgb, var(--gold) 7%, var(--surface-inset)); transform: translateY(-2px); } }
@media (max-width: 560px) { .third-party-games-modal { width: 100%; max-height: calc(100dvh - 20px); padding: 22px 15px 17px; }.third-party-modal-header { padding-right: 38px; }.third-party-game-list { grid-template-columns: 1fr; }.third-party-game-option { min-height: 82px; }.third-party-empty { min-height: 190px; } }
</style>
