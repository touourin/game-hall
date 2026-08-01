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
  if (isSetup.value) return isReady.value ? '你的棋子已锁定' : '点选两枚棋子即可交换位置'
  if (game.value.mode === 'flip' && !game.value.viewerSide) return '翻开任意暗棋，首翻颜色就是你的阵营'
  return `${game.value.modeLabel} · ${selfColorLabel.value}`
})

watch(() => props.snapshot.revision, () => { selected.value = null })

function key(row: number, column: number) { return `${row}-${column}` }
function isSelected(row: number, column: number) {
  return selected.value?.row === row && selected.value?.column === column
}
function isLatest(row: number, column: number) {
  const action = game.value.lastAction
  return action?.toRow === row && action?.toColumn === column
}
function isRail(row: number, column: number) {
  return [1, 5, 6, 10].includes(row) || ([0, 4].includes(column) && row >= 1 && row <= 10)
}

function choose(row: number, column: number) {
  if (props.snapshot.phase === 'finished') return
  const piece = game.value.board[row]?.[column] ?? null
  if (isSetup.value) {
    if (isReady.value || !piece?.revealed || piece.side !== game.value.viewerSide) return
    if (!selected.value) {
      selected.value = { row, column }
      return
    }
    if (isSelected(row, column)) {
      selected.value = null
      return
    }
    const from = selected.value
    selected.value = null
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
    void arcade.action('flip', { row, column })
    return
  }
  if (piece?.revealed && piece.side === game.value.viewerSide) {
    selected.value = isSelected(row, column) ? null : { row, column }
    return
  }
  if (selected.value) {
    const from = selected.value
    selected.value = null
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
        <template v-for="row in displayRows" :key="row">
          <button
            v-for="column in displayColumns"
            :key="key(row, column)"
            type="button"
            class="junqi-cell"
            :disabled="snapshot.phase === 'finished' || (isSetup ? isReady : !isMyTurn)"
            :class="{
              camp: campKeys.has(key(row, column)),
              headquarters: headquartersKeys.has(key(row, column)),
              rail: isRail(row, column),
              selected: isSelected(row, column),
              latest: isLatest(row, column),
              occupied: game.board[row][column],
            }"
            :aria-label="`第 ${row + 1} 行第 ${column + 1} 列`"
            @click="choose(row, column)"
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
              <small v-if="game.board[row][column]?.revealed && game.board[row][column]?.kind === 'flag'">旗</small>
            </span>
          </button>
        </template>
        <div class="river-label">战 线</div>
      </div>

      <aside class="junqi-side-panel surface">
        <div><small>当前玩法</small><strong>{{ game.modeLabel }}</strong></div>
        <div><small>你的阵营</small><strong :class="game.viewerSide ?? ''">{{ selfColorLabel }}</strong></div>
        <div><small>已行动</small><strong>{{ game.moveCount }} 次</strong></div>
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
.junqi-game { width: min(100%, 980px); margin: 0 auto; display: grid; gap: 16px; }
.junqi-status { padding: 14px 16px; display: grid; grid-template-columns: auto 1fr auto; gap: 12px; align-items: center; }
.junqi-status > span { width: 42px; aspect-ratio: 1; display: grid; place-items: center; border-radius: 12px; color: var(--gold); background: color-mix(in srgb, var(--gold) 10%, transparent); }
.junqi-status strong, .junqi-status small { display: block; }.junqi-status small { margin-top: 3px; color: var(--muted); }.junqi-status em { color: var(--gold); font-style: normal; font-weight: 800; }
.junqi-status.active { border-color: color-mix(in srgb, var(--gold) 34%, transparent); }
.junqi-layout { display: grid; grid-template-columns: minmax(320px, 520px) minmax(200px, 1fr); gap: 18px; align-items: start; justify-content: center; }
.junqi-board { position: relative; width: 100%; aspect-ratio: 5 / 9.2; padding: 14px; display: grid; grid-template-columns: repeat(5, 1fr); grid-template-rows: repeat(12, 1fr); gap: 5px; border: 2px solid #8d6836; border-radius: 18px; background: linear-gradient(155deg, #c7a96d, #a68148); box-shadow: 0 22px 48px #0007, 0 0 0 1px color-mix(in srgb, var(--gold) 24%, transparent); overflow: hidden; }
.junqi-board::after { content: ''; position: absolute; left: 0; right: 0; top: 50%; height: 7.5%; transform: translateY(-50%); pointer-events: none; background: #5e795d66; border-top: 1px solid #394f38aa; border-bottom: 1px solid #394f38aa; }
.river-label { position: absolute; z-index: 1; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #253b2b99; font-family: serif; font-weight: 900; letter-spacing: .8em; white-space: nowrap; pointer-events: none; }
.junqi-cell { position: relative; z-index: 2; min-width: 0; padding: 2px; display: grid; place-items: center; border: 1px solid #76572e80; border-radius: 7px; color: #47351e; background: #ead29b9c; }
.junqi-cell:disabled { opacity: 1; }
.junqi-cell.rail { border-width: 2px; border-color: #59401fc0; }
.junqi-cell.camp { border-radius: 50%; background: #d9c58f; }
.junqi-cell.headquarters { border-style: double; border-width: 3px; }
.junqi-cell.selected { outline: 3px solid var(--gold); outline-offset: 1px; transform: translateY(-1px); }
.junqi-cell.latest { box-shadow: inset 0 0 0 3px color-mix(in srgb, var(--gold) 54%, transparent); }
.terrain-label { font-size: clamp(8px, 1.7vw, 11px); font-weight: 900; opacity: .65; }
.junqi-piece { width: 90%; height: 88%; display: grid; place-items: center; align-content: center; border: 2px solid currentColor; border-radius: 7px; font-family: serif; font-weight: 900; background: #f3dfae; box-shadow: 0 3px 5px #33230b66; }
.junqi-piece b { font-size: clamp(10px, 2vw, 17px); line-height: 1; white-space: nowrap; }.junqi-piece small { margin-top: 2px; font-size: 8px; }
.junqi-piece.red { color: #a72e2b; }.junqi-piece.blue { color: #245b81; }.junqi-piece.hidden { color: #403523; background: linear-gradient(145deg, #6e5b3d, #403727); }
.junqi-piece.concealed { color: #f3db9b; border-color: #c5a85f; }
.junqi-side-panel { padding: 18px; display: grid; gap: 15px; }
.junqi-side-panel > div { padding-bottom: 12px; border-bottom: 1px solid var(--line); }.junqi-side-panel small, .junqi-side-panel strong { display: block; }.junqi-side-panel small { margin-bottom: 4px; color: var(--muted); }.junqi-side-panel strong { font-size: 18px; }.junqi-side-panel strong.red { color: #ec8a83; }.junqi-side-panel strong.blue { color: #82bee9; }
.junqi-side-panel summary { display: flex; align-items: center; gap: 6px; color: var(--gold); cursor: pointer; font-weight: 800; }.junqi-side-panel p { color: var(--muted); font-size: 13px; line-height: 1.6; }
.junqi-actions { display: flex; justify-content: center; gap: 10px; }.junqi-actions button:not(.arcade-danger-button) { padding: 11px 18px; display: inline-flex; align-items: center; gap: 7px; border: 1px solid var(--line); border-radius: 12px; color: var(--text); background: var(--surface); }.junqi-actions button.primary { color: #08271f; background: var(--green); }.junqi-actions button:disabled { opacity: .4; }
@media (max-width: 720px) {
  .junqi-layout { grid-template-columns: 1fr; }
  .junqi-board { width: min(100%, 470px); margin: 0 auto; padding: 8px; gap: 3px; border-radius: 13px; }
  .junqi-side-panel { grid-template-columns: repeat(3, 1fr); padding: 12px; gap: 8px; }
  .junqi-side-panel > div { padding: 0 6px 0 0; border-right: 1px solid var(--line); border-bottom: 0; }
  .junqi-side-panel details { grid-column: 1 / -1; }
  .junqi-status { grid-template-columns: auto 1fr; }.junqi-status em { grid-column: 2; }
}
@media (max-width: 400px) {
  .junqi-piece { border-width: 1px; }.junqi-piece b { font-size: 11px; }
  .junqi-side-panel strong { font-size: 14px; }
}
</style>
