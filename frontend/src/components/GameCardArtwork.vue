<script setup lang="ts">
import type { GameCatalogItem } from '../types/arcade'

defineProps<{ gameKey: GameCatalogItem['key'] }>()
</script>

<template>
  <span class="game-card-art" :class="`art-${gameKey}`" aria-hidden="true">
    <span v-if="gameKey === 'gomoku' || gameKey === 'go'" class="board-mini">
      <i class="stone stone-dark" /><i class="stone stone-light" /><i class="stone stone-accent" />
    </span>

    <span v-else-if="gameKey === 'xiangqi'" class="xiangqi-mini">
      <i>將</i><b /><em>楚河 · 汉界</em>
    </span>

    <span v-else-if="gameKey === 'poker' || gameKey === 'doudizhu'" class="card-fan">
      <i><b>{{ gameKey === 'poker' ? 'A' : '2' }}</b><em>♠</em></i>
      <i><b>{{ gameKey === 'poker' ? 'K' : 'A' }}</b><em>♥</em></i>
      <i v-if="gameKey === 'doudizhu'"><b>J</b><em>★</em></i>
    </span>

    <span v-else-if="gameKey === 'junqi'" class="junqi-mini">
      <i>旗</i><b /><em>军令如山</em>
    </span>

    <span v-else-if="gameKey === 'reaction'" class="reaction-mini">
      <i /><b>⚡</b><em>228 ms</em>
    </span>

    <span v-else-if="gameKey === 'schulte'" class="schulte-mini">
      <i v-for="number in [7, 2, 9, 4, 1, 6, 8, 5, 3]" :key="number">{{ number }}</i>
    </span>

    <span v-else-if="gameKey === 'minesweeper'" class="mine-mini">
      <i v-for="(cell, index) in ['1', '', '2', '', '✦', '', '2', '', '1']" :key="index">{{ cell }}</i>
    </span>

    <span v-else-if="gameKey === 'hanoi'" class="hanoi-mini">
      <i class="tower tower-one"><b /><b /><b /><b /></i>
      <i class="tower tower-two" /><i class="tower tower-three" />
      <em />
    </span>
  </span>
</template>

<style scoped>
.game-card-art { position: relative; width: 100%; min-height: 114px; display: grid; place-items: center; overflow: hidden; border: 1px solid color-mix(in srgb, var(--card-tone) 24%, var(--line)); border-radius: 13px; background: radial-gradient(circle at 50% 18%, color-mix(in srgb, var(--card-tone) 13%, transparent), transparent 50%), var(--surface-inset); color: var(--card-tone); }
.game-card-art::after { position: absolute; inset: 0; background: linear-gradient(135deg, rgba(255,255,255,.035), transparent 42%), repeating-linear-gradient(135deg, transparent 0 9px, rgba(255,255,255,.012) 9px 10px); content: ''; pointer-events: none; }

.board-mini { position: absolute; inset: 10px; background-image: linear-gradient(color-mix(in srgb, var(--card-tone) 30%, transparent) 1px, transparent 1px), linear-gradient(90deg, color-mix(in srgb, var(--card-tone) 30%, transparent) 1px, transparent 1px); background-size: 20% 20%; background-position: center; transform: perspective(170px) rotateX(12deg) rotateZ(-4deg); }
.stone { position: absolute; width: 22px; aspect-ratio: 1; border-radius: 50%; box-shadow: 0 4px 7px rgba(0,0,0,.48), inset -3px -3px 5px rgba(0,0,0,.32), inset 2px 2px 3px rgba(255,255,255,.25); }
.stone-dark { top: 38%; left: 31%; background: #101312; }.stone-light { top: 20%; left: 53%; background: #e6e1d4; }.stone-accent { top: 59%; left: 53%; background: #161a18; }
.art-go .stone-dark { top: 17%; left: 19%; }.art-go .stone-light { top: 58%; left: 35%; }.art-go .stone-accent { top: 38%; left: 67%; }

.xiangqi-mini { position: absolute; inset: 0; display: grid; place-items: center; background-image: linear-gradient(color-mix(in srgb, var(--card-tone) 18%, transparent) 1px, transparent 1px), linear-gradient(90deg, color-mix(in srgb, var(--card-tone) 18%, transparent) 1px, transparent 1px); background-size: 24px 24px; }
.xiangqi-mini i { z-index: 1; width: 58px; aspect-ratio: 1; display: grid; place-items: center; border: 3px double currentColor; border-radius: 50%; background: color-mix(in srgb, var(--card-tone) 18%, #121716); box-shadow: 0 10px 18px rgba(0,0,0,.4); font-family: "Songti SC", serif; font-size: 27px; font-style: normal; font-weight: 800; transform: rotate(7deg); }
.xiangqi-mini b { position: absolute; right: 0; left: 0; height: 24px; background: var(--surface-elevated); opacity: .9; }
.xiangqi-mini em { position: absolute; z-index: 1; right: 6px; bottom: 4px; color: var(--muted); font-size: 7px; font-style: normal; letter-spacing: .08em; }

.card-fan { position: relative; width: 92px; height: 82px; }
.card-fan i { position: absolute; bottom: -13px; left: 25px; width: 53px; height: 76px; border: 1px solid rgba(255,255,255,.48); border-radius: 7px; padding: 6px; color: #23231f; background: #eee8db; box-shadow: 0 9px 18px rgba(0,0,0,.32); font-style: normal; transform: rotate(-13deg); }
.card-fan i:nth-child(2) { left: 47px; color: #a84e43; transform: rotate(12deg); }.card-fan i:nth-child(3) { left: 4px; color: #8c6831; transform: rotate(-27deg); }
.card-fan b,.card-fan em { display: block; font-size: 15px; line-height: 1; }.card-fan em { margin-top: 3px; font-style: normal; }

.junqi-mini { position: relative; width: 94px; height: 80px; }
.junqi-mini b { position: absolute; top: 6px; left: 29px; width: 3px; height: 66px; background: currentColor; box-shadow: 0 0 12px color-mix(in srgb, var(--card-tone) 45%, transparent); transform: rotate(-7deg); }
.junqi-mini i { position: absolute; z-index: 1; top: 8px; left: 31px; width: 53px; height: 36px; display: grid; place-items: center; clip-path: polygon(0 0,100% 18%,83% 100%,0 82%); color: var(--accent-contrast); background: var(--card-tone); font-family: "Songti SC", serif; font-style: normal; font-weight: 900; transform: rotate(-7deg); }
.junqi-mini em { position: absolute; bottom: 0; left: 0; color: var(--muted); font-size: 8px; font-style: normal; letter-spacing: .12em; }

.reaction-mini { position: relative; width: 92px; aspect-ratio: 1; display: grid; place-items: center; }
.reaction-mini i,.reaction-mini i::before { position: absolute; inset: 7px; border: 1px solid currentColor; border-radius: 50%; content: ''; opacity: .28; }.reaction-mini i::before { inset: 11px; opacity: .65; }
.reaction-mini b { font-size: 36px; filter: drop-shadow(0 0 10px currentColor); }.reaction-mini em { position: absolute; right: -8px; bottom: 6px; border-radius: 999px; padding: 3px 6px; color: var(--text); background: var(--surface-elevated); font-size: 7px; font-style: normal; }

.schulte-mini,.mine-mini { width: 86px; display: grid; grid-template-columns: repeat(3,1fr); gap: 2px; padding: 3px; border: 1px solid color-mix(in srgb, var(--card-tone) 28%, transparent); background: color-mix(in srgb, var(--card-tone) 9%, transparent); transform: rotate(-3deg); }
.schulte-mini i,.mine-mini i { aspect-ratio: 1; display: grid; place-items: center; background: var(--surface-elevated); color: var(--text-soft); font-size: 9px; font-style: normal; font-weight: 850; }
.schulte-mini i:nth-child(5) { color: var(--accent-contrast); background: var(--card-tone); }.mine-mini i:nth-child(5) { color: var(--card-tone); font-size: 15px; }

.hanoi-mini { position: relative; width: 112px; height: 84px; }
.hanoi-mini > em { position: absolute; right: 3px; bottom: 7px; left: 3px; height: 4px; border-radius: 4px; background: color-mix(in srgb, var(--card-tone) 65%, var(--surface)); }
.tower { position: absolute; bottom: 10px; width: 3px; height: 57px; background: color-mix(in srgb, var(--card-tone) 58%, transparent); }.tower-one { left: 25px; }.tower-two { left: 55px; }.tower-three { left: 85px; }
.tower-one b { position: absolute; left: 50%; height: 8px; border-radius: 6px; background: var(--card-tone); transform: translateX(-50%); }.tower-one b:nth-child(1) { bottom: 1px; width: 42px; }.tower-one b:nth-child(2) { bottom: 10px; width: 34px; }.tower-one b:nth-child(3) { bottom: 19px; width: 27px; }.tower-one b:nth-child(4) { bottom: 28px; width: 19px; }

@media (max-width: 680px) {
  .game-card-art { min-height: 92px; }
  .stone { width: 18px; }
}
</style>
