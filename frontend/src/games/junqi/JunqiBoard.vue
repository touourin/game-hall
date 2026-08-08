<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Check, Dices, Flag, Info } from '@lucide/vue'
import { useArcadeStore } from '../../stores/arcade'
import type { ArcadeSnapshot } from '../../types/arcade'

type Side = 'red' | 'blue'
interface PublicPiece {
  id: string | null
  side: Side | null
  kind: string | null
  label: string | null
  revealed: boolean
}
interface Position { row: number; column: number }

const props = defineProps<{ snapshot: ArcadeSnapshot }>()
const arcade = useArcadeStore()
const selected = ref<Position | null>(null)
const pendingTarget = ref<Position | null>(null)
const pendingFlip = ref<Position | null>(null)

const game = computed(() => props.snapshot.game as {
  mode: 'dark' | 'flip'
  modeLabel: string
  board: Array<Array<PublicPiece | null>>
  turnPlayerId: string | null
  colors: Record<string, Side>
  viewerSide: Side | null
  setupReady: Record<string, boolean>
  lastAction: null | {
    type: string
    fromRow?: number
    fromColumn?: number
    toRow?: number
    toColumn?: number
    message: string
    label?: string
  }
  moveCount: number
  terrain: { camps: number[][]; headquarters: number[][] }
})
const isMyTurn = computed(() => game.value.turnPlayerId === props.snapshot.self.id)
const isSetup = computed(() => props.snapshot.phase === 'setup')
const isReady = computed(() => game.value.setupReady[props.snapshot.self.id] ?? false)
const campKeys = computed(() => new Set(game.value.terrain.camps.map(([row, column]) => `${row}-${column}`)))
const headquartersKeys = computed(() => new Set(game.value.terrain.headquarters.map(([row, column]) => `${row}-${column}`)))
const displayRows = computed(() => {
  const rows = Array.from({ length: 12 }, (_, row) => row)
  return game.value.viewerSide === 'blue' ? rows.reverse() : rows
})
const displayColumns = computed(() => {
  const columns = Array.from({ length: 5 }, (_, column) => column)
  return game.value.viewerSide === 'blue' ? columns.reverse() : columns
})
const selfColorLabel = computed(() => {
  if (game.value.viewerSide === 'red') return '红方'
  if (game.value.viewerSide === 'blue') return '蓝方'
  return '阵营尚未确定'
})
const statusTitle = computed(() => {
  if (props.snapshot.phase === 'finished') return props.snapshot.winReason ?? '本局结束'
  if (isSetup.value) return isReady.value ? '已确认，等待对手布阵' : '秘密布阵'
  return isMyTurn.value ? '轮到你行动' : '等待对手行动'
})
const statusHint = computed(() => {
  if (pendingFlip.value) return `预览翻开第 ${pendingFlip.value.row + 1} 行第 ${pendingFlip.value.column + 1} 列 · 再点一次确认`
  if (pendingTarget.value) return `预览目标第 ${pendingTarget.value.row + 1} 行第 ${pendingTarget.value.column + 1} 列 · 再点一次确认`
  if (isSetup.value) return isReady.value ? '你的棋子已锁定' : '点选两枚棋子即可交换位置'
  if (game.value.mode === 'flip' && !game.value.viewerSide) return '翻开任意暗棋，首翻颜色就是你的阵营'
  return `${game.value.modeLabel} · ${selfColorLabel.value}`
})

watch(() => props.snapshot.revision, () => {
  selected.value = null
  pendingTarget.value = null
  pendingFlip.value = null
})

function key(row: number, column: number) { return `${row}-${column}` }
function isSelected(row: number, column: number) {
  return selected.value?.row === row && selected.value?.column === column
}
function isPending(row: number, column: number) {
  return pendingTarget.value?.row === row && pendingTarget.value?.column === column
    || pendingFlip.value?.row === row && pendingFlip.value?.column === column
}
function usesTouchConfirmation(event: MouseEvent) {
  return ['touch', 'pen'].includes((event as PointerEvent).pointerType ?? '')
}
function isLatest(row: number, column: number) {
  const action = game.value.lastAction
  return action?.toRow === row && action?.toColumn === column
}
function isLastFrom(row: number, column: number) {
  const action = game.value.lastAction
  return action?.fromRow === row && action?.fromColumn === column
}
function isRail(row: number, column: number) {
  return [1, 5, 6, 10].includes(row) || ([0, 4].includes(column) && row >= 1 && row <= 10)
}

function choose(row: number, column: number, event: MouseEvent) {
  if (props.snapshot.phase === 'finished' || arcade.busy) return
  const piece = game.value.board[row]?.[column] ?? null
  if (isSetup.value) {
    if (isReady.value || !piece?.revealed || piece.side !== game.value.viewerSide) return
    if (!selected.value) {
      selected.value = { row, column }
      pendingTarget.value = null
      return
    }
    if (isSelected(row, column)) {
      selected.value = null
      pendingTarget.value = null
      return
    }
    if (usesTouchConfirmation(event) && !isPending(row, column)) {
      pendingTarget.value = { row, column }
      return
    }
    const from = selected.value
    selected.value = null
    pendingTarget.value = null
    void arcade.action('swap', {
      fromRow: from.row,
      fromColumn: from.column,
      toRow: row,
      toColumn: column,
    })
    return
  }
  if (!isMyTurn.value) return
  if (game.value.mode === 'flip' && piece && !piece.revealed) {
    selected.value = null
    pendingTarget.value = null
    if (usesTouchConfirmation(event) && !isPending(row, column)) {
      pendingFlip.value = { row, column }
      return
    }
    pendingFlip.value = null
    void arcade.action('flip', { row, column })
    return
  }
  if (piece?.revealed && piece.side === game.value.viewerSide) {
    selected.value = isSelected(row, column) ? null : { row, column }
    pendingTarget.value = null
    pendingFlip.value = null
    return
  }
  if (selected.value) {
    if (usesTouchConfirmation(event) && !isPending(row, column)) {
      pendingTarget.value = { row, column }
      pendingFlip.value = null
      return
    }
    const from = selected.value
    selected.value = null
    pendingTarget.value = null
    pendingFlip.value = null
    void arcade.action('move', {
      fromRow: from.row,
      fromColumn: from.column,
      toRow: row,
      toColumn: column,
    })
  }
}
</script>

<template>
  <section class="junqi-game">
    <header class="junqi-status surface" :class="{ active: isMyTurn || isSetup }">
      <span><Flag :size="23" /></span>
      <div><strong>{{ statusTitle }}</strong><small>{{ statusHint }}</small></div>
      <em v-if="game.lastAction && !isSetup">{{ game.lastAction.message }}</em>
    </header>

    <div class="junqi-layout">
      <div class="junqi-board" :class="`viewer-${game.viewerSide ?? 'unknown'}`" aria-label="军旗棋盘">
        <div class="territory-label enemy"><span>敌方阵地</span><small>ENEMY SECTOR</small></div>

        <div class="junqi-field">
          <div class="junqi-mountain-pass" aria-hidden="true"></div>
          <svg class="junqi-route-map" viewBox="0 0 4 12" preserveAspectRatio="none" aria-hidden="true">
            <g class="road-network">
              <path d="M0 0H4 M0 1H4 M0 2H4 M0 3H4 M0 4H4 M0 5H4 M0 7H4 M0 8H4 M0 9H4 M0 10H4 M0 11H4 M0 12H4" />
              <path d="M0 0V5 M1 0V5 M2 0V5 M3 0V5 M4 0V5 M0 7V12 M1 7V12 M2 7V12 M3 7V12 M4 7V12 M0 5V7 M2 5V7 M4 5V7" />
              <path d="M1 1L0 0 M1 1L2 0 M1 1L0 2 M1 1L2 2 M3 1L2 0 M3 1L4 0 M3 1L2 2 M3 1L4 2 M2 2L1 3 M2 2L3 3 M1 3L0 2 M1 3L0 4 M1 3L2 4 M3 3L4 2 M3 3L2 4 M3 3L4 4" />
              <path d="M1 11L0 12 M1 11L2 12 M1 11L0 10 M1 11L2 10 M3 11L2 12 M3 11L4 12 M3 11L2 10 M3 11L4 10 M2 10L1 9 M2 10L3 9 M1 9L0 10 M1 9L0 8 M1 9L2 8 M3 9L4 10 M3 9L2 8 M3 9L4 8" />
            </g>
            <g class="rail-network rail-bed">
              <path d="M0 1H4 M0 5H4 M0 7H4 M0 11H4 M0 1V11 M4 1V11 M2 5V7" />
            </g>
            <g class="rail-network rail-core">
              <path d="M0 1H4 M0 5H4 M0 7H4 M0 11H4 M0 1V11 M4 1V11 M2 5V7" />
            </g>
          </svg>

          <div class="junqi-special-space frontline first" aria-hidden="true">前线</div>
          <div class="junqi-special-space mountain first" aria-hidden="true">山界</div>
          <div class="junqi-special-space frontline second" aria-hidden="true">前线</div>
          <div class="junqi-special-space mountain second" aria-hidden="true">山界</div>
          <div class="junqi-special-space frontline third" aria-hidden="true">前线</div>

          <template v-for="(row, displayRowIndex) in displayRows" :key="row">
            <button
              v-for="(column, displayColumnIndex) in displayColumns"
              :key="key(row, column)"
              type="button"
              class="junqi-cell"
              :style="{
                gridRow: displayRowIndex < 6 ? displayRowIndex + 1 : displayRowIndex + 2,
                gridColumn: displayColumnIndex + 1,
              }"
              :disabled="snapshot.phase === 'finished' || arcade.busy || (isSetup ? isReady : !isMyTurn)"
              :class="{
                camp: campKeys.has(key(row, column)),
                headquarters: headquartersKeys.has(key(row, column)),
                rail: isRail(row, column),
                selected: isSelected(row, column),
                confirming: isPending(row, column),
                latest: isLatest(row, column),
                'last-from': isLastFrom(row, column),
                occupied: game.board[row][column],
              }"
              :aria-label="`第 ${row + 1} 行第 ${column + 1} 列${campKeys.has(key(row, column)) ? '，行营' : headquartersKeys.has(key(row, column)) ? '，大本营' : isRail(row, column) ? '，铁路兵站' : '，公路兵站'}`"
              @click="choose(row, column, $event)"
            >
              <span v-if="campKeys.has(key(row, column)) && !game.board[row][column]" class="terrain-label">行营</span>
              <span v-else-if="headquartersKeys.has(key(row, column)) && !game.board[row][column]" class="terrain-label">大本营</span>
              <span
                v-if="game.board[row][column]"
                class="junqi-piece"
                :class="[
                  game.board[row][column]?.side ?? 'hidden',
                  { concealed: !game.board[row][column]?.revealed },
                ]"
              >
                <b>{{ game.board[row][column]?.revealed ? game.board[row][column]?.label : '軍' }}</b>
                <small>{{ game.board[row][column]?.revealed && game.board[row][column]?.kind === 'flag' ? '军旗' : game.board[row][column]?.revealed ? '部队' : '密令' }}</small>
              </span>
            </button>
          </template>
        </div>

        <div class="territory-label self"><span>我方阵地</span><small>YOUR SECTOR</small></div>
      </div>

      <aside class="junqi-side-panel surface">
        <header><small>FIELD BRIEFING</small><strong>战场情报</strong></header>
        <div class="junqi-metrics">
          <div><small>当前玩法</small><strong>{{ game.modeLabel }}</strong></div>
          <div><small>你的阵营</small><strong :class="game.viewerSide ?? ''">{{ selfColorLabel }}</strong></div>
          <div><small>已行动</small><strong>{{ game.moveCount }} 次</strong></div>
        </div>
        <section class="terrain-legend" aria-label="棋盘地形图例">
          <h3>地形图例</h3>
          <div><i class="legend-line road"></i><span><b>公路线</b><small>每次移动一站</small></span></div>
          <div><i class="legend-line railway"></i><span><b>铁路线</b><small>可直线快速行军</small></span></div>
          <div><i class="legend-node camp"></i><span><b>行营</b><small>驻军不会被攻击</small></span></div>
          <div><i class="legend-node headquarters"></i><span><b>大本营</b><small>进入后不能移动</small></span></div>
        </section>
        <details>
          <summary><Info :size="16" />玩法提示</summary>
          <p>军旗、地雷不能移动；大本营内棋子不能移动；行营中的棋子不能被攻击。</p>
          <p>铁路可直线远行，工兵还能在铁路转弯；工兵排雷，炸弹与目标同归于尽。</p>
        </details>
      </aside>
    </div>

    <div v-if="isSetup" class="junqi-actions">
      <button type="button" :disabled="isReady" @click="arcade.action('randomize')"><Dices :size="18" />重新随机</button>
      <button type="button" class="primary" :disabled="isReady" @click="arcade.action('ready')"><Check :size="18" />确认布阵</button>
    </div>
    <div v-else-if="snapshot.phase === 'playing'" class="junqi-actions">
      <button type="button" class="arcade-danger-button" @click="arcade.action('resign')"><Flag :size="17" />认输</button>
    </div>
  </section>
</template>

<style scoped>
.junqi-game { --junqi-red: #a93631; --junqi-blue: #245d82; width: min(100%, 1040px); margin: 0 auto; display: grid; gap: 16px; }
.junqi-status { position: relative; overflow: hidden; padding: 14px 16px; display: grid; grid-template-columns: auto 1fr auto; gap: 12px; align-items: center; }
.junqi-status::after { content: ''; position: absolute; inset: 0 0 auto; height: 2px; opacity: 0; background: linear-gradient(90deg, transparent, var(--gold), transparent); transition: opacity .2s ease; }
.junqi-status > span { width: 42px; aspect-ratio: 1; display: grid; place-items: center; border: 1px solid color-mix(in srgb, var(--gold) 24%, transparent); border-radius: 9px; color: var(--gold); background: color-mix(in srgb, var(--gold) 9%, transparent); transform: rotate(45deg); }
.junqi-status > span :deep(svg) { transform: rotate(-45deg); }
.junqi-status strong, .junqi-status small { display: block; }.junqi-status small { margin-top: 3px; color: var(--muted); }.junqi-status em { color: var(--gold); font-style: normal; font-weight: 800; }
.junqi-status.active { border-color: color-mix(in srgb, var(--gold) 34%, transparent); }.junqi-status.active::after { opacity: 1; }
.junqi-layout { display: grid; grid-template-columns: minmax(340px, 560px) minmax(220px, 1fr); gap: 20px; align-items: start; justify-content: center; }

.junqi-board { --junqi-self-accent: var(--junqi-red); --junqi-enemy-accent: var(--junqi-blue); position: relative; isolation: isolate; width: 100%; box-sizing: border-box; overflow: hidden; padding: 12px clamp(12px, 2.4vw, 20px) 16px; border: 3px solid var(--game-board-frame, #765025); border-radius: 10px; background-color: var(--game-board-surface, #c19a58); background-image: linear-gradient(145deg, color-mix(in srgb, white 8%, transparent), transparent 32%, color-mix(in srgb, var(--game-board-frame, #765025) 11%, transparent)), linear-gradient(90deg, color-mix(in srgb, var(--game-board-frame, #765025) 8%, transparent) 1px, transparent 1px), var(--game-board-texture, repeating-linear-gradient(88deg, transparent 0 27px, rgba(83,45,15,.05) 28px)); background-size: auto, 32px 100%, auto; box-shadow: inset 0 0 0 2px var(--game-board-highlight, rgba(255,225,155,.35)), inset 0 0 0 8px color-mix(in srgb, var(--game-board-frame, #765025) 28%, transparent), inset 0 0 42px rgba(24,18,9,.25), 0 22px 50px #0007, 0 0 0 1px color-mix(in srgb, var(--gold) 26%, transparent); }
.junqi-board.viewer-blue { --junqi-self-accent: var(--junqi-blue); --junqi-enemy-accent: var(--junqi-red); }
.junqi-board::before, .junqi-board::after { content: ''; position: absolute; z-index: 0; top: 10px; bottom: 10px; width: 5px; border-block: 1px solid color-mix(in srgb, var(--game-board-line, #4c3e27) 42%, transparent); opacity: .7; }
.junqi-board::before { left: 7px; border-left: 2px solid color-mix(in srgb, var(--game-board-line, #4c3e27) 65%, transparent); }.junqi-board::after { right: 7px; border-right: 2px solid color-mix(in srgb, var(--game-board-line, #4c3e27) 65%, transparent); }
.territory-label { position: relative; z-index: 4; min-height: 34px; display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-inline: 9px; color: var(--game-board-label, #48351e); text-transform: uppercase; }
.territory-label::before { content: ''; width: 4px; height: 14px; flex: 0 0 auto; border-radius: 2px; background: var(--territory-accent); box-shadow: 0 0 10px color-mix(in srgb, var(--territory-accent) 36%, transparent); }
.territory-label span { font-family: "Songti SC", "STSong", serif; font-size: 12px; font-weight: 900; letter-spacing: .24em; }.territory-label small { font-size: 8px; font-weight: 800; letter-spacing: .16em; opacity: .62; }
.territory-label span { margin-right: auto; }.territory-label.enemy { --territory-accent: var(--junqi-enemy-accent); border-bottom: 1px solid color-mix(in srgb, var(--junqi-enemy-accent) 34%, var(--game-board-line, #4c3e27)); }.territory-label.self { --territory-accent: var(--junqi-self-accent); border-top: 1px solid color-mix(in srgb, var(--junqi-self-accent) 34%, var(--game-board-line, #4c3e27)); }

.junqi-field { position: relative; isolation: isolate; width: 100%; aspect-ratio: 5 / 8.75; display: grid; grid-template-columns: repeat(5, 1fr); grid-template-rows: repeat(13, 1fr); }
.junqi-mountain-pass { position: relative; z-index: 0; grid-row: 7; grid-column: 1 / -1; align-self: stretch; margin-block: 7%; border-block: 1px solid color-mix(in srgb, var(--game-board-line, #59401f) 32%, transparent); background-image: linear-gradient(135deg, transparent 42%, color-mix(in srgb, var(--game-board-line, #59401f) 18%, transparent) 43% 52%, transparent 53%), linear-gradient(45deg, transparent 42%, color-mix(in srgb, var(--game-board-highlight, #ead29b) 34%, transparent) 43% 52%, transparent 53%), linear-gradient(90deg, color-mix(in srgb, var(--game-board-frame, #765025) 8%, transparent), color-mix(in srgb, var(--game-board-highlight, #ead29b) 12%, transparent), color-mix(in srgb, var(--game-board-frame, #765025) 8%, transparent)); background-position: 0 50%, 18px 50%, 0 0; background-size: 36px 28px, 36px 28px, auto; box-shadow: inset 0 1px color-mix(in srgb, white 10%, transparent), inset 0 -1px color-mix(in srgb, black 12%, transparent); pointer-events: none; }
.junqi-route-map { pointer-events: none; position: absolute; z-index: 1; inset: 3.8462% 10%; width: 80%; height: 92.3076%; overflow: visible; }
.junqi-route-map path { fill: none; vector-effect: non-scaling-stroke; stroke-linecap: square; stroke-linejoin: round; }
.road-network path { stroke: color-mix(in srgb, var(--game-board-line, #5e4627) 55%, transparent); stroke-width: 1.35; }
.rail-network { filter: drop-shadow(0 1px color-mix(in srgb, white 12%, transparent)); }.rail-network path { stroke: var(--game-board-line, #4d3920); }.rail-bed path { stroke-width: 8; opacity: .84; }.rail-core path { stroke: color-mix(in srgb, var(--game-board-surface, #c19a58) 84%, white); stroke-width: 3.2; stroke-dasharray: 2.5 2; }
.junqi-special-space { position: relative; z-index: 2; grid-row: 7; place-self: center; box-sizing: border-box; display: grid; place-items: center; color: var(--game-board-label, #47351e); background: color-mix(in srgb, var(--game-board-surface, #c19a58) 84%, var(--game-board-highlight, #ead29b)); font-family: "Songti SC", "STSong", serif; font-size: clamp(7px, 1.25vw, 10px); font-weight: 900; pointer-events: none; }
.junqi-special-space.frontline { width: 43%; aspect-ratio: 1; border: 2px solid color-mix(in srgb, var(--game-board-line, #59401f) 82%, transparent); border-radius: 2px; box-shadow: inset 0 0 0 1px color-mix(in srgb, white 14%, transparent), 0 2px 4px color-mix(in srgb, black 18%, transparent); }.junqi-special-space.mountain { width: 48%; aspect-ratio: 1; border: 4px double color-mix(in srgb, var(--game-board-line, #59401f) 78%, transparent); border-radius: 50%; box-shadow: inset 0 0 10px color-mix(in srgb, var(--game-board-line, #59401f) 12%, transparent); opacity: .82; }
.junqi-special-space.first { grid-column: 1; }.junqi-special-space.mountain.first { grid-column: 2; }.junqi-special-space.second { grid-column: 3; }.junqi-special-space.mountain.second { grid-column: 4; }.junqi-special-space.third { grid-column: 5; }

.junqi-cell { position: relative; z-index: 3; min-width: 0; min-height: 0; display: grid; place-items: center; appearance: none; -webkit-appearance: none; touch-action: manipulation; padding: 0; border: 0; color: var(--game-board-label, #47351e); background: transparent; }
.junqi-cell::before { content: ''; position: absolute; z-index: 0; width: 72%; height: 52%; box-sizing: border-box; border: 1px solid color-mix(in srgb, var(--game-board-line, #59401f) 72%, transparent); border-radius: 2px; background-color: color-mix(in srgb, var(--game-board-surface, #c19a58) 86%, var(--game-board-highlight, #ead29b)); background-image: linear-gradient(145deg, color-mix(in srgb, white 9%, transparent), transparent 48%); box-shadow: inset 0 0 0 1px color-mix(in srgb, white 10%, transparent), inset 0 -2px color-mix(in srgb, var(--game-board-line, #59401f) 12%, transparent), 0 2px 3px rgba(31,20,7,.18); }
.junqi-cell:disabled { opacity: 1; }.junqi-cell:not(:disabled) { cursor: pointer; }.junqi-cell:not(:disabled):hover::before { filter: brightness(1.08); }
.junqi-cell.rail::before { border-width: 2px; border-color: color-mix(in srgb, var(--game-board-line, #59401f) 82%, transparent); }
.junqi-cell.camp::before { width: 48%; height: auto; aspect-ratio: 1; border: 3px double color-mix(in srgb, var(--game-board-line, #59401f) 78%, transparent); border-radius: 50%; background-color: color-mix(in srgb, #667a49 24%, var(--game-board-surface, #c19a58)); background-image: radial-gradient(circle at 38% 32%, color-mix(in srgb, white 13%, transparent), transparent 42%); box-shadow: inset 0 0 0 2px color-mix(in srgb, var(--game-board-highlight, #d9c58f) 24%, transparent), 0 2px 4px rgba(31,20,7,.2); }
.junqi-cell.headquarters::before { width: 76%; height: 58%; border: 2px solid color-mix(in srgb, var(--game-board-line, #59401f) 88%, #15130f); border-radius: 2px; background: color-mix(in srgb, var(--game-board-line, #59401f) 72%, #17140f); box-shadow: inset 0 0 0 2px color-mix(in srgb, var(--game-board-surface, #c19a58) 25%, transparent), 0 2px 3px rgba(0,0,0,.22); clip-path: polygon(12% 18%,50% 0,88% 18%,100% 18%,100% 100%,0 100%,0 18%); }
.junqi-cell.headquarters .terrain-label { color: color-mix(in srgb, var(--game-board-surface, #c19a58) 72%, white); text-shadow: 0 1px rgba(0,0,0,.4); }.junqi-cell.headquarters .terrain-label::before { content: '★'; display: block; margin-bottom: 1px; font-size: .82em; }
.junqi-cell.selected::after, .junqi-cell.latest::after, .junqi-cell.last-from::after { content: ''; position: absolute; z-index: 4; width: 88%; height: 75%; border: 3px solid var(--gold); border-radius: 7px; box-shadow: 0 0 0 2px color-mix(in srgb, var(--gold) 22%, transparent), 0 0 18px color-mix(in srgb, var(--gold) 55%, transparent); pointer-events: none; }
.junqi-cell.confirming::after { content: ''; position: absolute; z-index: 5; width: 88%; height: 75%; border: 3px solid var(--gold); border-radius: 7px; background: color-mix(in srgb, var(--gold) 14%, transparent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--gold) 22%, transparent), 0 0 18px color-mix(in srgb, var(--gold) 58%, transparent); pointer-events: none; }
.junqi-cell.latest::after { width: 80%; height: 64%; border-width: 2px; border-color: #df8637; box-shadow: 0 0 12px rgba(223,134,55,.42); }.junqi-cell.last-from::after { width: 18%; height: auto; aspect-ratio: 1; border: 0; border-radius: 50%; background: #df8637; box-shadow: 0 0 0 3px rgba(223,134,55,.22); }
.terrain-label { position: relative; z-index: 1; font-family: "Songti SC", "STSong", serif; font-size: clamp(7px, 1.35vw, 10px); font-weight: 900; letter-spacing: .05em; opacity: .76; }
.junqi-piece { position: relative; z-index: 3; width: 82%; height: 64%; box-sizing: border-box; overflow: hidden; display: grid; place-items: center; align-content: center; border: 2px solid currentColor; border-radius: 5px; font-family: "Songti SC", "STSong", serif; font-weight: 900; background: var(--game-piece-surface, #f3dfae); box-shadow: inset 0 0 0 1px var(--game-piece-rim, transparent), inset 0 2px color-mix(in srgb, white 34%, transparent), inset 0 -6px 9px rgba(49,27,7,.17), 0 4px 7px #0007; transition: transform .14s ease, filter .14s ease, box-shadow .14s ease; }
.junqi-piece::before { content: ''; position: absolute; inset: 3px; border: 1px solid currentColor; border-radius: 2px; opacity: .3; pointer-events: none; }.junqi-piece b { position: relative; font-size: clamp(10px, 2vw, 18px); line-height: 1; white-space: nowrap; }.junqi-piece small { position: relative; margin-top: 3px; font-family: system-ui, sans-serif; font-size: clamp(5px, .9vw, 7px); line-height: 1; letter-spacing: .14em; opacity: .62; }
.junqi-piece.red { color: var(--junqi-red); }.junqi-piece.blue { color: var(--junqi-blue); }.junqi-piece.hidden { color: var(--game-card-back-accent, #f3db9b); background: var(--game-card-back, linear-gradient(145deg, #6e5b3d, #403727)); }.junqi-piece.concealed { color: var(--game-card-back-accent, #f3db9b); border-color: var(--game-card-back-accent, #c5a85f); background: var(--game-card-back, linear-gradient(145deg, #6e5b3d, #403727)); }.junqi-cell.selected .junqi-piece { transform: translateY(-3px) scale(1.04); filter: brightness(1.08); box-shadow: inset 0 0 0 1px var(--game-piece-rim, transparent), 0 8px 12px #0008, 0 0 16px color-mix(in srgb, var(--gold) 48%, transparent); }

.junqi-side-panel { overflow: hidden; padding: 0; display: grid; align-content: start; gap: 0; }
.junqi-side-panel > header { padding: 18px; border-bottom: 1px solid var(--line); background: linear-gradient(135deg, color-mix(in srgb, var(--gold) 8%, transparent), transparent 58%); }.junqi-side-panel > header small, .junqi-side-panel > header strong { display: block; }.junqi-side-panel > header small { margin-bottom: 5px; color: var(--gold); font-size: 9px; letter-spacing: .18em; }.junqi-side-panel > header strong { font-size: 20px; }
.junqi-metrics { padding: 16px 18px; display: grid; gap: 12px; }.junqi-metrics > div { padding-bottom: 11px; border-bottom: 1px solid var(--line); }.junqi-metrics > div:last-child { padding-bottom: 0; border-bottom: 0; }.junqi-metrics small, .junqi-metrics strong { display: block; }.junqi-metrics small { margin-bottom: 4px; color: var(--muted); }.junqi-metrics strong { font-size: 17px; }.junqi-metrics strong.red { color: #ec8a83; }.junqi-metrics strong.blue { color: #82bee9; }
.terrain-legend { padding: 16px 18px; display: grid; gap: 11px; border-block: 1px solid var(--line); background: rgba(0,0,0,.08); }.terrain-legend h3 { margin: 0 0 2px; color: var(--muted); font-size: 11px; letter-spacing: .12em; }.terrain-legend > div { display: grid; grid-template-columns: 34px 1fr; gap: 10px; align-items: center; }.terrain-legend span b, .terrain-legend span small { display: block; }.terrain-legend span b { font-size: 12px; }.terrain-legend span small { margin-top: 2px; color: var(--muted); font-size: 10px; }
.legend-line { position: relative; display: block; width: 31px; height: 9px; }.legend-line::before { content: ''; position: absolute; top: 50%; left: 0; right: 0; border-top: 1px solid var(--muted); }.legend-line.railway { border-block: 2px solid var(--gold); }.legend-line.railway::before { border-color: transparent; background: repeating-linear-gradient(90deg, var(--gold) 0 2px, transparent 2px 6px); height: 100%; top: 0; }
.legend-node { justify-self: center; display: block; width: 18px; height: 18px; border: 2px double var(--gold); }.legend-node.camp { border-radius: 50%; }.legend-node.headquarters { width: 25px; height: 17px; border-style: solid; background: color-mix(in srgb, var(--gold) 12%, transparent); clip-path: polygon(12% 22%,50% 0,88% 22%,100% 22%,100% 100%,0 100%,0 22%); }
.junqi-side-panel details { padding: 15px 18px 18px; }.junqi-side-panel summary { display: flex; align-items: center; gap: 6px; color: var(--gold); cursor: pointer; font-weight: 800; }.junqi-side-panel p { margin-bottom: 0; color: var(--muted); font-size: 13px; line-height: 1.6; }
.junqi-actions { display: flex; justify-content: center; gap: 10px; }.junqi-actions button:not(.arcade-danger-button) { padding: 11px 18px; display: inline-flex; align-items: center; gap: 7px; border: 1px solid var(--line); border-radius: 12px; color: var(--text); background: var(--surface); }.junqi-actions button.primary { color: #08271f; background: var(--green); }.junqi-actions button:disabled { opacity: .4; }
@media (max-width: 720px) {
  .junqi-layout { grid-template-columns: 1fr; }
  .junqi-board { width: min(100%, 520px); margin: 0 auto; padding-inline: clamp(9px, 3vw, 16px); }
  .junqi-side-panel { width: min(100%, 520px); margin: 0 auto; }
  .junqi-metrics { grid-template-columns: repeat(3, 1fr); gap: 8px; }.junqi-metrics > div { padding: 0 8px 0 0; border-right: 1px solid var(--line); border-bottom: 0; }.junqi-metrics > div:last-child { border-right: 0; }
  .terrain-legend { grid-template-columns: 1fr 1fr; }.terrain-legend h3 { grid-column: 1 / -1; }
  .junqi-status { grid-template-columns: auto 1fr; }.junqi-status em { grid-column: 2; }
}
@media (max-width: 400px) {
  .junqi-board { border-width: 2px; }.territory-label { min-height: 29px; }.territory-label small { display: none; }
  .junqi-piece { width: 86%; height: 67%; border-width: 1px; }.junqi-piece::before { inset: 2px; }.junqi-piece b { font-size: 10px; }.junqi-piece small { display: none; }
  .junqi-special-space.frontline { width: 48%; border-width: 1px; }.junqi-special-space.mountain { width: 52%; border-width: 3px; }
  .junqi-cell.camp::before { width: 52%; border-width: 2px; }.junqi-cell.headquarters::before { width: 80%; border-width: 1px; }
  .junqi-metrics strong { font-size: 13px; }.terrain-legend { grid-template-columns: 1fr; }.terrain-legend h3 { grid-column: auto; }
}
</style>
